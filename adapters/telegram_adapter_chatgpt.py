from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
from application.consultar_facturas_usecase import ConsultarFacturasUseCase  # Nueva importación
from application.detectar_intencion_chatgpt_usecase import DetectarIntencionChatGPTUseCase
import re
import logging
import json
from datetime import datetime
from infrastructure.database import get_db_session
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TelegramAdapterChatGPT:
    def __init__(self, token, detectar_intencion_usecase: DetectarIntencionChatGPTUseCase,
                 reclamo_usecase: RegistrarReclamoUseCase, actualizar_usecase: ActualizarUsuarioUseCase,
                 consulta_estado_usecase: ConsultarEstadoReclamoUseCase,
                 consulta_reclamo_usecase: ConsultarReclamoUseCase,
                 redis_client, app):
        self.token = token
        self.detectar_intencion_usecase = detectar_intencion_usecase
        session_db1 = get_db_session(app, bind='db1')
        session_db2 = get_db_session(app, bind='db2')
        self.usuario_repository = SQLAlchemyUsuarioRepository(session_db1, session_db2)
        self.reclamo_usecase = reclamo_usecase if reclamo_usecase else RegistrarReclamoUseCase(
            SQLAlchemyReclamoRepository(session_db2),
            self.usuario_repository
        )
        self.actualizar_usecase = actualizar_usecase if actualizar_usecase else ActualizarUsuarioUseCase(
            self.usuario_repository
        )
        self.consulta_estado_usecase = consulta_estado_usecase if consulta_estado_usecase else ConsultarEstadoReclamoUseCase(
            SQLAlchemyReclamoRepository(session_db2),
            self.usuario_repository
        )
        self.consulta_reclamo_usecase = consulta_reclamo_usecase if consulta_reclamo_usecase else ConsultarReclamoUseCase(
            SQLAlchemyReclamoRepository(session_db2)
        )
        self.consultar_facturas_usecase = ConsultarFacturasUseCase(self.usuario_repository)  # Nuevo caso de uso
        self.redis_client = redis_client
        self.app = ApplicationBuilder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("reset", self.reset))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        self.redis_client.delete(f"user:{user_id}:historial")
        self.redis_client.delete(f"user:{user_id}:estado")
        await update.message.reply_text(
            "¡Hola! Soy DECSA, tu asistente virtual oficial. Estoy aquí para ayudarte con cualquier problema o consulta sobre nuestros servicios eléctricos. ¿En qué puedo ayudarte hoy? Puedes hacer un reclamo, actualizar tus datos, consultar el estado de un reclamo o ver tu factura."
        )

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        self.redis_client.delete(f"user:{user_id}:historial")
        self.redis_client.delete(f"user:{user_id}:estado")
        await update.message.reply_text(
            "Conversación reiniciada. ¿En qué puedo ayudarte ahora? Puedo asistirte con reclamos, actualizar datos, consultar estados o facturas."
        )

    def preprocess_text(self, text):
        logging.info(f"Preprocesando texto original: {text}")
        text = text.lower()
        text = re.sub(r'\bk\w*', lambda m: m.group(0).replace('k', 'qu') if 'k' in m.group(0) else m.group(0).replace('k', 'c'), text)
        text = re.sub(r'\bz\w*', lambda m: m.group(0).replace('z', 's') if 'z' in m.group(0) else m.group(0), text)
        text = re.sub(r'\bx\w*', lambda m: m.group(0).replace('x', 's') if 'x' in m.group(0) else m.group(0).replace('x', 'j'), text)
        text = re.sub(r'\b(k|q)uier[oa]|kere\b', 'quiero', text)
        text = re.sub(r'\b(ak|ac)tua(l|ll)?(l|ll)?iz(ar|er)|aktuali[zs]ar\b', 'actualizar', text)
        text = re.sub(r'\b(rek|rec|rel)al[mo]|reclamoo?\b', 'reclamo', text)
        text = re.sub(r'\b(kom|con|kol)sul(tar|tar)|consul[dt]ar\b', 'consultar', text)
        text = re.sub(r'\b(ha|as)cer|aser\b', 'hacer', text)
        text = re.sub(r'\b(direk|dier|dir)ec(c|k)ion|direcsion\b', 'direccion', text)
        text = re.sub(r'\b(est|es)tadoo?\b', 'estado', text)
        text = re.sub(r'(\w*?)([aeiou])\2(\w*)', r'\1\2\3', text)
        text = re.sub(r'(\w)r(\w)e', r'\1er\2', text)
        logging.info(f"Texto preprocesado: {text}")
        return text

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = str(update.effective_user.id)
            texto_usuario = update.message.text.strip().lower()
            texto_preprocesado = self.preprocess_text(texto_usuario)

            historial_clave = f"user:{user_id}:historial"
            estado_clave = f"user:{user_id}:estado"

            self.redis_client.rpush(historial_clave, f"Usuario: {texto_usuario}")
            historial = " | ".join(self.redis_client.lrange(historial_clave, -5, -1) or [])
            logging.info(f"Historial actual: {historial}")

            estado = self.redis_client.hgetall(estado_clave) or {"fase": "inicio"}
            logging.info(f"Estado actual: {estado}")

            if texto_usuario in ["cancelar", "salir"] and estado["fase"] != "inicio":
                self.redis_client.hset(estado_clave, "fase", "inicio")
                self.redis_client.hdel(estado_clave, "dni")
                self.redis_client.hdel(estado_clave, "accion")
                self.redis_client.hdel(estado_clave, "nombre")
                self.redis_client.hdel(estado_clave, "campo_actualizar")
                self.redis_client.hdel(estado_clave, "descripcion")
                await update.message.reply_text(
                    "✅ Entendido, he detenido el proceso. ¿En qué puedo ayudarte ahora? Puedo asistirte con reclamos, actualizar datos, consultar estados o facturas."
                )
                logging.info("Proceso cancelado por el usuario")
                return
            elif texto_usuario in ["cancelar", "salir"] and estado["fase"] == "inicio":
                await update.message.reply_text(
                    "No hay ningún proceso activo para cancelar. ¿En qué puedo ayudarte hoy? Puedo asistirte con reclamos, actualizar datos, consultar estados o facturas."
                )
                return

            if estado["fase"] == "inicio":
                logging.info("Fase inicio: Detectando intención con ChatGPT")
                respuesta_cruda = self.detectar_intencion_usecase.ejecutar_con_historial(texto_preprocesado, historial)
                try:
                    resultado = json.loads(respuesta_cruda)
                    intencion = resultado.get("intencion", "Conversar")
                    respuesta = resultado.get("respuesta", "No entendí bien tu mensaje. ¿En qué puedo ayudarte hoy? Puedes decirme si quieres hacer un reclamo, actualizar datos, consultar algo o ver tu factura.")
                except (json.JSONDecodeError, TypeError) as e:
                    logging.warning(f"Error al parsear respuesta: {respuesta_cruda}, Error: {str(e)}")
                    intencion = "Conversar"
                    respuesta = "No entendí bien tu mensaje. ¿En qué puedo ayudarte hoy? Puedes decirme si quieres hacer un reclamo, actualizar datos, consultar algo o ver tu factura."

                logging.info(f"Intención detectada: {intencion}, Respuesta: {respuesta}")
                await update.message.reply_text(respuesta)

                if intencion == "Reclamo":
                    self.redis_client.hset(estado_clave, "fase", "pedir_dni")
                    self.redis_client.hset(estado_clave, "accion", "reclamo")
                elif intencion == "Actualizar":
                    self.redis_client.hset(estado_clave, "fase", "seleccionar_dato")
                elif intencion == "Consultar":
                    self.redis_client.hset(estado_clave, "fase", "pedir_dni")
                    self.redis_client.hset(estado_clave, "accion", "consultar")
                elif intencion == "ConsultarFacturas":  # Nueva intención
                    self.redis_client.hset(estado_clave, "fase", "pedir_dni")
                    self.redis_client.hset(estado_clave, "accion", "consultar_facturas")

            elif estado["fase"] == "seleccionar_dato":
                opciones_validas = {"calle": "CALLE", "barrio": "BARRIO", "celular": "CELULAR", "teléfono": "CELULAR", "correo": "EMAIL", "mail": "EMAIL"}
                if texto_usuario not in opciones_validas:
                    await update.message.reply_text(
                        "No reconocí eso. Por favor, dime 'calle', 'barrio', 'celular' o 'correo'. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                    return
                campo_actualizar = opciones_validas[texto_usuario]
                self.redis_client.hset(estado_clave, "fase", "pedir_dni")
                self.redis_client.hset(estado_clave, "accion", "actualizar")
                self.redis_client.hset(estado_clave, "campo_actualizar", campo_actualizar)
                await update.message.reply_text(
                    f"Entendido, quieres actualizar tu {texto_usuario}. Por favor, dame tu DNI para continuar. Di 'cancelar' o 'salir' para detener el proceso."
                )

            elif estado["fase"] == "pedir_dni":
                if not re.match(r'^\d+$', texto_usuario):
                    await update.message.reply_text(
                        "Eso no parece un DNI válido. Por favor, ingresa solo números. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                    return
                usuario_db1 = self.actualizar_usecase.usuario_repository.obtener_de_db1(texto_usuario)
                if usuario_db1:
                    # Tomamos el primer registro de la lista para el nombre
                    primer_registro = usuario_db1[0]
                    nombre = f"{primer_registro['Apellido'].strip()} {primer_registro['Nombre'].strip()}"
                    self.redis_client.hset(estado_clave, "fase", "confirmar_dni")
                    self.redis_client.hset(estado_clave, "dni", texto_usuario)
                    self.redis_client.hset(estado_clave, "nombre", nombre)
                    await update.message.reply_text(
                        f"¿Eres {nombre}? Dime 'sí' o 'no' para confirmar. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                else:
                    usuario_db2 = self.actualizar_usecase.usuario_repository.obtener_por_dni(texto_usuario)
                    if usuario_db2:
                        nombre = usuario_db2.NOMBRE_COMPLETO.strip()
                        self.redis_client.hset(estado_clave, "fase", "confirmar_dni")
                        self.redis_client.hset(estado_clave, "dni", texto_usuario)
                        self.redis_client.hset(estado_clave, "nombre", nombre)
                        await update.message.reply_text(
                            f"¿Eres {nombre}? Dime 'sí' o 'no' para confirmar. Di 'cancelar' o 'salir' para detener el proceso."
                        )
                    else:
                        await update.message.reply_text(
                            "No encontré a nadie con ese DNI. Verifica el número e inténtalo de nuevo. Di 'cancelar' o 'salir' para detener el proceso."
                        )

            elif estado["fase"] == "confirmar_dni":
                if texto_usuario not in ["sí", "si", "no"]:
                    await update.message.reply_text(
                        "Por favor, dime 'sí' o 'no' para confirmar. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                    return
                if texto_usuario == "no":
                    self.redis_client.hset(estado_clave, "fase", "inicio")
                    await update.message.reply_text(
                        "Entendido, parece que el DNI no es correcto. Dime otro cuando quieras."
                    )
                    return
                dni = estado.get("dni")
                if estado.get("accion") == "reclamo":
                    self.redis_client.hset(estado_clave, "fase", "solicitar_descripcion")
                    await update.message.reply_text(
                        f"Gracias por confirmar, {estado.get('nombre')}. Cuéntame qué problema tienes para registrar tu reclamo. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                elif estado.get("accion") == "consultar":
                    self.redis_client.hset(estado_clave, "fase", "consultar_reclamos")
                    await update.message.reply_text(
                        f"Gracias, {estado.get('nombre')}. Aquí están tus últimos 5 reclamos:\n{self.format_reclamos(dni)}\nSi quieres detalles de uno, dime su ID. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                elif estado.get("accion") == "actualizar":
                    campo = estado.get("campo_actualizar")
                    usuario_db2 = self.actualizar_usecase.usuario_repository.obtener_por_dni(dni)
                    current_value = getattr(usuario_db2, campo) if usuario_db2 and hasattr(usuario_db2, campo) else "No disponible"
                    self.redis_client.hset(estado_clave, "fase", "confirmar_actualizacion")
                    await update.message.reply_text(
                        f"Tu {campo.lower()} actual es: *{current_value}*. Dime el nuevo valor para actualizarlo. Di 'cancelar' o 'salir' para detener el proceso."
                    )
                elif estado.get("accion") == "consultar_facturas":  # Nueva acción
                    resultado, status = self.consultar_facturas_usecase.ejecutar(dni)
                    if status == 200:
                        factura = resultado["factura"]
                        mensaje = (f"Factura de {factura['Nombre']} (DNI: {dni}):\n"
                                  f"📋 *Código Suministro*: {factura['CodigoSuministro']}\n"
                                  f"📄 *N° Comprobante*: {factura['NumeroComprobante']}\n"
                                  f"📅 *Fecha Emisión*: {factura['FechaEmision']}\n"
                                  f"✅ *Estado*: {factura['Estado']}\n"
                                  f"💰 *Total*: ${factura['Total']:.2f}\n"
                                  f"⏰ *Vencimiento*: {factura['Vencimiento']}\n"
                                  f"🏠 *Dirección*: {factura['Calle']}, {factura['Barrio']}\n"
                                  f"🔍 *Observación Postal*: {factura['ObservacionPostal']}\n"
                                  f"⚡ *Medidor*: {factura['NumeroMedidor']}\n"
                                  f"📆 *Período*: {factura['Periodo']}\n"
                                  f"🔋 *Consumo*: {factura['Consumo']} kWh")
                        await update.message.reply_text(mensaje)
                    else:
                        await update.message.reply_text("No encontré tu factura. Verifica el DNI e intenta de nuevo.")
                    self.redis_client.hset(estado_clave, "fase", "inicio")
                    await update.message.reply_text("¿En qué más puedo ayudarte? Puedo asistirte con reclamos, datos, estados o facturas.")

            elif estado["fase"] == "solicitar_descripcion":
                if len(texto_usuario.strip()) < 3:
                    await update.message.reply_text(
                        "Por favor, dame más detalles (al menos 3 caracteres). Di 'cancelar' o 'salir' para detener el proceso."
                    )
                    return
                self.redis_client.hset(estado_clave, "fase", "ejecutar_accion")
                self.redis_client.hset(estado_clave, "descripcion", texto_usuario)
                await self.handle_message(update, context)

            elif estado["fase"] == "consultar_reclamos":
                if re.match(r'^\d+$', texto_usuario):
                    id_reclamo = int(texto_usuario)
                    respuesta, codigo = self.consulta_reclamo_usecase.ejecutar(id_reclamo)
                    if codigo == 200:
                        reclamo = respuesta["reclamo"]
                        cliente = respuesta["cliente"]
                        fecha_reclamo = reclamo.get('FECHA_RECLAMO', 'No disponible')
                        if fecha_reclamo != 'No disponible':
                            try:
                                fecha_reclamo_dt = datetime.fromisoformat(fecha_reclamo.replace('Z', '+00:00'))
                                fecha_reclamo = fecha_reclamo_dt.strftime("%d/%m/%Y %H:%M")
                            except ValueError:
                                fecha_reclamo = "No disponible"
                        calle = cliente.get('direccion', 'No disponible')
                        barrio = cliente.get('barrio', 'No disponible')
                        direccion = f"calle {calle}, barrio {barrio}" if calle != 'No disponible' and barrio != 'No disponible' else (calle if calle != 'No disponible' else barrio)
                        await update.message.reply_text(
                            f"Detalles del reclamo ID {id_reclamo}:\n"
                            f"- Descripción: {reclamo.get('DESCRIPCION', 'No disponible')}\n"
                            f"- Estado: {reclamo.get('ESTADO', 'No disponible')}\n"
                            f"- Fecha de Reclamo: {fecha_reclamo}\n"
                            f"- Cliente: {cliente.get('nombre', 'No disponible')} (DNI: {cliente.get('dni', 'No disponible')})\n"
                            f"- Dirección: {direccion if direccion else 'No disponible'}"
                        )
                        self.redis_client.hset(estado_clave, "fase", "inicio")
                    else:
                        await update.message.reply_text(
                            f"No encontré ese reclamo. Intenta con otro ID. Di 'cancelar' o 'salir' para detener el proceso."
                        )
                else:
                    await update.message.reply_text(
                        "Por favor, dame un ID de reclamo (solo números). Di 'cancelar' o 'salir' para detener el proceso."
                    )

            elif estado["fase"] == "confirmar_actualizacion":
                self.redis_client.hset(estado_clave, "fase", "ejecutar_accion")
                self.redis_client.hset(estado_clave, "valor_actualizar", texto_usuario)
                await self.handle_message(update, context)

            elif estado["fase"] == "ejecutar_accion":
                dni = estado.get("dni")
                accion = estado.get("accion")
                descripcion = estado.get("descripcion", "")
                valor_actualizar = estado.get("valor_actualizar", "")
                nombre = estado.get("nombre")

                if accion == "reclamo":
                    resultado, status = self.reclamo_usecase.ejecutar(dni, descripcion)
                    if status == 201:
                        reclamo_id = resultado["id_reclamo"]
                        respuesta = f"Listo, {nombre}. Tu reclamo está registrado con ID: {reclamo_id}, Estado: Pendiente. Resumen: {descripcion}"
                    else:
                        respuesta = "Lo siento, no pude registrar tu reclamo ahora. ¿Intentamos de nuevo?"
                elif accion == "actualizar":
                    campo = estado.get("campo_actualizar")
                    resultado, status = self.actualizar_usecase.ejecutar(dni, {campo: valor_actualizar})
                    if status == 200:
                        usuario_db2 = self.actualizar_usecase.usuario_repository.obtener_por_dni(dni)
                        usuario_db1 = self.actualizar_usecase.usuario_repository.obtener_de_db1(dni) if not usuario_db2 else None
                        if usuario_db2:
                            respuesta = (f"✅ ¡Actualización exitosa, {nombre}!\n\n✔️ Datos actualizados:\n"
                                        f"📛 Nombre: {usuario_db2.NOMBRE_COMPLETO}\n"
                                        f"📍 Calle: {usuario_db2.CALLE}\n"
                                        f"🏘️ Barrio: {usuario_db2.BARRIO}\n"
                                        f"📱 Teléfono: {usuario_db2.CELULAR}\n"
                                        f"✉️ Correo: {usuario_db2.EMAIL}")
                        elif usuario_db1:
                            respuesta = (f"✅ ¡Actualización exitosa, {nombre}!\n\n✔️ Datos actualizados:\n"
                                        f"📛 Nombre: {usuario_db1['Apellido']} {usuario_db1['Nombre']}\n"
                                        f"📍 Calle: {usuario_db1.get('Calle', 'No disponible')}\n"
                                        f"🏘️ Barrio: {usuario_db1.get('Barrio', 'No disponible')}\n"
                                        f"📱 Teléfono: {usuario_db1.get('Telefono', 'No disponible')}\n"
                                        f"✉️ Correo: {usuario_db1.get('Email', 'No disponible')}")
                        else:
                            respuesta = "Actualización exitosa, pero no pude recuperar tus datos actualizados."
                    else:
                        respuesta = "No pude actualizar eso ahora. ¿Probamos otra vez?"
                else:
                    respuesta = "Algo salió mal. ¿En qué más puedo ayudarte?"

                await update.message.reply_text(respuesta)
                await update.message.reply_text(
                    "¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
                )
                self.redis_client.hset(estado_clave, "fase", "inicio")
                self.redis_client.hdel(estado_clave, "descripcion")
                self.redis_client.hdel(estado_clave, "valor_actualizar")

        except Exception as e:
            logging.error(f"Error en handle_message: {str(e)}")
            await update.message.reply_text(
                f"Uy, algo falló: {str(e)}. Intentemos de nuevo."
            )
            self.redis_client.hset(estado_clave, "fase", "inicio")

    def run(self):
        logging.info("🚀 Bot de Telegram (ChatGPT) corriendo...")
        self.app.run_polling()

    def format_reclamos(self, dni=None, is_single=False):
        if is_single and dni:
            logging.warning("format_reclamos llamado con is_single=True y dni, pero se espera un id_reclamo")
            return "Función no implementada para reclamo individual por DNI"
        else:
            respuesta, codigo = self.consulta_estado_usecase.ejecutar(dni) if dni else (None, 404)
            if codigo == 200:
                if "mensaje" in respuesta:
                    return respuesta["mensaje"]
                reclamos = respuesta.get("reclamos", [])
                if not reclamos:
                    return "No tienes reclamos registrados recientemente."
                return "\n".join([
                    f"ID: {r['ID_RECLAMO']}, Estado: {r['ESTADO']}, Descripción: {r['DESCRIPCION'][:50]}{'...' if len(r['DESCRIPCION']) > 50 else ''}"
                    for r in reclamos
                ])
            return "No pude obtener tus reclamos. Intenta de nuevo."