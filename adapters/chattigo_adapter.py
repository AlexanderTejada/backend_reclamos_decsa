# adapters/chattigo_adapter.py
import json
import logging
import re
from typing import Dict, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from pydantic import BaseModel
from application.detectar_intencion_chatgpt_usecase import DetectarIntencionChatGPTUseCase
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
from application.consultar_facturas_usecase import ConsultarFacturasUseCase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ChattigoMessage(BaseModel):
    user_id: str
    message: dict


class ChattigoResponse(BaseModel):
    response: str
    user_id: str


class ChattigoAdapter:
    def __init__(self, detectar_intencion: DetectarIntencionChatGPTUseCase, reclamo: RegistrarReclamoUseCase,
                 actualizar: ActualizarUsuarioUseCase, consulta_estado: ConsultarEstadoReclamoUseCase,
                 consulta_reclamo: ConsultarReclamoUseCase, consultar_facturas: ConsultarFacturasUseCase,
                 redis_client):
        self.detectar_intencion = detectar_intencion
        self.reclamo = reclamo
        self.actualizar = actualizar
        self.consulta_estado = consulta_estado
        self.consulta_reclamo = consulta_reclamo
        self.consultar_facturas = consultar_facturas
        self.redis_client = redis_client
        self.memory_reset_interval = timedelta(hours=24)  # Intervalo para resetear la memoria (24 horas)
        self.process_timeout = timedelta(minutes=5)  # Timeout del proceso (5 minutos)
        self.last_memory_reset = datetime.now()  # Última vez que se reseteó la memoria
        self.last_interaction = {}  # Almacena la última interacción de cada usuario (en memoria)

        # Verificar que el cliente de Redis esté inicializado correctamente
        try:
            self.redis_client.ping()
            logging.info("✅ Cliente de Redis inicializado correctamente")
        except Exception as e:
            logging.error(f"❌ Error al inicializar el cliente de Redis: {str(e)}")
            raise

    async def handle_message(self, request: Request) -> Dict[str, str]:
        try:
            # Leer el cuerpo de la solicitud una sola vez
            payload = await request.json()
            # Loguear el cuerpo de la solicitud
            logging.info(f"Mensaje recibido: {json.dumps(payload)}")

            mensaje = ChattigoMessage(**payload)
            texto_usuario = mensaje.message.get("text", "").strip().lower()
            user_id = mensaje.user_id

            logging.info(f"Procesando mensaje - User ID: {user_id}, Texto: {texto_usuario}")

            historial_clave = f"user:{user_id}:historial"
            estado_clave = f"user:{user_id}:estado"

            # Resetear la memoria si ha pasado el intervalo de tiempo
            current_time = datetime.now()
            if (current_time - self.last_memory_reset) >= self.memory_reset_interval:
                self.redis_client.flushdb()  # Limpia toda la base de datos de Redis
                self.last_interaction.clear()
                self.last_memory_reset = current_time
                logging.info("🌟 Memoria de Redis reseteada para ahorrar recursos")

            # Manejo del historial en Redis
            self.redis_client.rpush(historial_clave, f"Usuario: {texto_usuario}")
            # Mantener solo los últimos 5 mensajes
            self.redis_client.ltrim(historial_clave, -5, -1)
            historial = " | ".join(self.redis_client.lrange(historial_clave, 0, -1) or [])

            # Manejo del estado en Redis
            estado = self.redis_client.hgetall(estado_clave)
            if not estado:
                estado = {"fase": "inicio", "user_id": user_id}
                self.redis_client.hset(estado_clave, mapping=estado)

            # Verificar timeout del proceso
            if user_id in self.last_interaction:
                last_interaction_time = self.last_interaction[user_id]
                if (current_time - last_interaction_time) >= self.process_timeout and estado.get("fase",
                                                                                                 "inicio") != "inicio":
                    self.redis_client.hset(estado_clave, "fase", "inicio")
                    self.redis_client.hdel(estado_clave, "dni")
                    self.redis_client.hdel(estado_clave, "accion")
                    self.redis_client.hdel(estado_clave, "nombre")
                    self.redis_client.hdel(estado_clave, "campo_actualizar")
                    self.redis_client.hdel(estado_clave, "descripcion")
                    logging.info(f"Usuario {user_id} sacado del proceso por inactividad")
                    return {
                        "response": "⏰ Han pasado 5 minutos sin actividad. Te he sacado del proceso.\n\n✨ ¿En qué puedo ayudarte ahora?",
                        "user_id": user_id}

            # Actualizar la última interacción
            self.last_interaction[user_id] = current_time

            logging.info(f"Estado actual: {estado}")

            if texto_usuario in ["cancelar", "salir"]:
                respuesta = self._handle_cancel(estado, estado_clave)
            else:
                respuesta = await self._process_phase(texto_usuario, estado, historial, estado_clave)

            # Agregar la opción de salir si está dentro de un proceso
            if estado.get("fase", "inicio") != "inicio":
                respuesta += "\n\n Escribi 'cancelar' o 'salir' para detener el proceso."
            else:
                respuesta += "\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."

            logging.info(f"Enviando respuesta - User ID: {user_id}, Respuesta: {respuesta}")
            return {"response": respuesta, "user_id": user_id}

        except HTTPException as he:
            raise he
        except Exception as e:
            logging.error(f"Error en handle_message: {str(e)}")
            return {"response": f"❌ Algo falló: {str(e)}. Intentemos de nuevo.", "user_id": user_id}

    def _preprocess_text(self, text: str) -> str:
        logging.info(f"Preprocesando texto original: {text}")
        text = text.lower()
        text = re.sub(r'\bk\w*',
                      lambda m: m.group(0).replace('k', 'qu') if 'k' in m.group(0) else m.group(0).replace('k', 'c'),
                      text)
        text = re.sub(r'\bz\w*', lambda m: m.group(0).replace('z', 's') if 'z' in m.group(0) else m.group(0), text)
        text = re.sub(r'\bx\w*',
                      lambda m: m.group(0).replace('x', 's') if 'x' in m.group(0) else m.group(0).replace('x', 'j'),
                      text)
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

    def _handle_cancel(self, estado: dict, estado_clave: str) -> str:
        if estado.get("fase", "inicio") != "inicio":
            self.redis_client.hset(estado_clave, "fase", "inicio")
            self.redis_client.hdel(estado_clave, "dni")
            self.redis_client.hdel(estado_clave, "accion")
            self.redis_client.hdel(estado_clave, "nombre")
            self.redis_client.hdel(estado_clave, "campo_actualizar")
            self.redis_client.hdel(estado_clave, "descripcion")
            return "✅ Proceso cancelado con éxito."
        return "ℹ️ No hay ningún proceso activo para cancelar."

    async def _process_phase(self, texto: str, estado: dict, historial: str, estado_clave: str) -> str:
        if estado.get("fase", "inicio") == "inicio":
            return await self._process_inicio(texto, historial, estado_clave)
        elif estado["fase"] == "seleccionar_dato":
            return self._process_seleccionar_dato(texto, estado, estado_clave)
        elif estado["fase"] == "pedir_dni":
            return await self._process_pedir_dni(texto, estado, estado_clave)
        elif estado["fase"] == "confirmar_dni":
            return await self._process_confirmar_dni(texto, estado, estado_clave)
        elif estado["fase"] == "solicitar_descripcion":
            return await self._process_solicitar_descripcion(texto, estado, estado_clave)
        elif estado["fase"] == "consultar_reclamos":
            return await self._process_consultar_reclamos(texto, estado, estado_clave)
        elif estado["fase"] == "confirmar_actualizacion":
            return await self._process_confirmar_actualizacion(texto, estado, estado_clave)
        return "❓ Algo salió mal. ¿En qué puedo ayudarte?"

    async def _process_inicio(self, texto: str, historial: str, estado_clave: str) -> str:
        intencion, respuesta = await self._detectar_intencion(texto, historial)

        # Lógica de respaldo para detectar intenciones si el modelo falla
        texto_lower = texto.lower()
        if intencion == "Conversar" or intencion not in ["Reclamo", "Actualizar", "Consultar", "ConsultarFacturas"]:
            if "reclamo" in texto_lower and (
                    "hacer" in texto_lower or "quiero" in texto_lower or "problema" in texto_lower):
                intencion = "Reclamo"
                respuesta = (
                    "💡 Lamentamos mucho escuchar que estás teniendo problemas con nuestro servicio. "
                    "Para ayudarte con tu reclamo, por favor, dime tu número de DNI. "
                    "¡Estaremos atentos para resolverlo lo antes posible! 🙏"
                )
            elif "actualizar" in texto_lower or "cambiar" in texto_lower:
                intencion = "Actualizar"
                respuesta = (
                    "📋 ¿Qué dato te gustaría actualizar hoy?\n"
                    "🏠 Calle\n"
                    "🏘️ Barrio\n"
                    "📱 Celular\n"
                    "✉️ Correo\n"
                    "Por favor, elige una opción (por ejemplo, escribe 'calle')."
                )
            elif ("consultar" in texto_lower or "ver" in texto_lower) and "reclamo" in texto_lower:
                intencion = "Consultar"
                respuesta = (
                    "📋 ¡Hola! Entiendo que deseas ver tus reclamos. "
                    "Para ayudarte con eso, por favor proporciona tu número de DNI. ✨ ¡Gracias!"
                )
            elif "factura" in texto_lower or ("ver" in texto_lower and "factura" in texto_lower):
                intencion = "ConsultarFacturas"
                respuesta = "📄 Por favor, dame tu DNI para consultar tu factura. ✨"

        if intencion == "Reclamo":
            self.redis_client.hset(estado_clave, "fase", "pedir_dni")
            self.redis_client.hset(estado_clave, "accion", "reclamo")
            return (
                "💡 Lamentamos mucho escuchar que estás teniendo problemas con nuestro servicio. "
                "Para ayudarte con tu reclamo, por favor, dime tu número de DNI. "
                "¡Estaremos atentos para resolverlo lo antes posible! 🙏"
            )
        elif intencion == "Actualizar":
            self.redis_client.hset(estado_clave, "fase", "seleccionar_dato")
            return (
                "📋 ¿Qué dato te gustaría actualizar hoy?\n"
                "🏠 Calle\n"
                "🏘️ Barrio\n"
                "📱 Celular\n"
                "✉️ Correo\n"
                "Por favor, elige una opción (por ejemplo, escribe 'calle')."
            )
        elif intencion == "Consultar":
            self.redis_client.hset(estado_clave, "fase", "pedir_dni")
            self.redis_client.hset(estado_clave, "accion", "consultar")
            return (
                "📋 ¡Hola! Entiendo que deseas ver tus reclamos. "
                "Para ayudarte con eso, por favor proporciona tu número de DNI. ✨ ¡Gracias!"
            )
        elif intencion == "ConsultarFacturas":
            self.redis_client.hset(estado_clave, "fase", "pedir_dni")
            self.redis_client.hset(estado_clave, "accion", "consultar_facturas")
            return "📄 Por favor, dame tu DNI para consultar tu factura. ✨"
        return respuesta

    async def _detectar_intencion(self, texto: str, historial: str) -> Tuple[str, str]:
        respuesta_cruda = self.detectar_intencion.ejecutar_con_historial(texto, historial)
        try:
            resultado = json.loads(respuesta_cruda)
            return resultado.get("intencion", "Conversar"), resultado.get("respuesta",
                                                                          "No entendí bien. ¿En qué te ayudo? Decime si querés un reclamo, actualizar datos, consultar algo o ver tu factura.")
        except json.JSONDecodeError:
            logging.warning(f"Respuesta de ChatGPT no es JSON válido: {respuesta_cruda}")
            return "Conversar", "No entendí bien. ¿En qué te ayudo? Decime si querés un reclamo, actualizar datos, consultar algo o ver tu factura."

    def _process_seleccionar_dato(self, texto: str, estado: dict, estado_clave: str) -> str:
        opciones_validas = {"calle": "CALLE", "barrio": "BARRIO", "celular": "CELULAR", "teléfono": "CELULAR",
                            "correo": "EMAIL", "mail": "EMAIL"}
        if texto not in opciones_validas:
            return (
                "❓ No reconocí eso. Por favor, elige una opción válida:\n"
                "🏠 Calle\n"
                "🏘️ Barrio\n"
                "📱 Celular\n"
                "✉️ Correo\n"
                "Escribe la opción que deseas (por ejemplo, 'calle')."
            )
        campo_actualizar = opciones_validas[texto]
        self.redis_client.hset(estado_clave, "fase", "pedir_dni")
        self.redis_client.hset(estado_clave, "accion", "actualizar")
        self.redis_client.hset(estado_clave, "campo_actualizar", campo_actualizar)
        return f"✨ Entendido, quieres actualizar tu {texto}. Por favor, dame tu DNI para continuar."

    async def _process_pedir_dni(self, texto: str, estado: dict, estado_clave: str) -> str:
        if not re.match(r'^\d+$', texto):
            return "❌ Eso no parece un DNI válido. Por favor, ingresa solo números."

        # Buscar al usuario por DNI usando el usuario_repository del caso de uso
        usuario_db1 = self.actualizar.usuario_repository.obtener_de_db1(texto)
        nombre = "Usuario Desconocido"
        if usuario_db1:
            primer_registro = usuario_db1[0]
            nombre = f"{primer_registro['Apellido'].strip()} {primer_registro['Nombre'].strip()}"
        else:
            usuario_db2 = self.actualizar.usuario_repository.obtener_por_dni(texto)
            if usuario_db2:
                nombre = usuario_db2.NOMBRE_COMPLETO.strip()

        self.redis_client.hset(estado_clave, "fase", "confirmar_dni")
        self.redis_client.hset(estado_clave, "dni", texto)
        self.redis_client.hset(estado_clave, "nombre", nombre)
        return f"👤 ¿Eres {nombre}? Dime 'sí' o 'no' para confirmar."

    async def _process_confirmar_dni(self, texto: str, estado: dict, estado_clave: str) -> str:
        if texto not in ["sí", "si", "no"]:
            return "❓ Por favor, dime 'sí' o 'no' para confirmar."
        if texto == "no":
            self.redis_client.hset(estado_clave, "fase", "inicio")
            return "ℹ️ Entendido, parece que el DNI no es correcto. Dime otro cuando quieras."
        dni = estado.get("dni")
        accion = estado.get("accion")
        nombre = estado.get("nombre", "Usuario")
        if accion == "reclamo":
            if not self.reclamo:
                return "❌ Funcionalidad no disponible: registrar_reclamo_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
            self.redis_client.hset(estado_clave, "fase", "solicitar_descripcion")
            return f"✅ Gracias por confirmar, {nombre}. Cuéntame qué problema tienes para registrar tu reclamo."
        elif accion == "actualizar":
            if not self.actualizar:
                return "❌ Funcionalidad no disponible: actualizar_usuario_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
            campo = estado.get("campo_actualizar")
            self.redis_client.hset(estado_clave, "fase", "confirmar_actualizacion")
            return f"✨ Dime el nuevo valor para tu {campo.lower()}."
        elif accion == "consultar":
            if not self.consulta_estado:
                return "❌ Funcionalidad no disponible: consultar_estado_reclamo_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
            self.redis_client.hset(estado_clave, "fase", "consultar_reclamos")
            return f"✅ Gracias, {nombre}. Aquí están tus últimos 5 reclamos:\n{await self._format_reclamos(dni)}\n🔍 Dime el ID de uno para más detalles."
        elif accion == "consultar_facturas":
            if not self.consultar_facturas:
                return "❌ Funcionalidad no disponible: consultar_facturas_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
            resultado, status = self.consultar_facturas.ejecutar(dni)
            if status == 200:
                factura = resultado["facturas"][0]
                respuesta = (f"📄 Factura de {factura['Nombre']} (DNI: {dni}):\n"
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
                self.redis_client.hset(estado_clave, "fase", "inicio")
                return respuesta
            self.redis_client.hset(estado_clave, "fase", "inicio")
            return "❌ No encontré tu factura. Verifica el DNI e intenta de nuevo."

    async def _process_solicitar_descripcion(self, texto: str, estado: dict, estado_clave: str) -> str:
        if len(texto.strip()) < 3:
            return "❓ Por favor, dame más detalles (mínimo 3 caracteres)."
        dni = estado.get("dni")
        if not self.reclamo:
            return "❌ Funcionalidad no disponible: registrar_reclamo_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
        resultado, status = self.reclamo.ejecutar(dni, texto)
        if status == 201:
            reclamo_id = resultado["id_reclamo"]
            nombre = estado.get("nombre", "Usuario")
            respuesta = (f"✅ Listo, {nombre}. Tu reclamo está registrado con éxito:\n"
                         f"🆔 ID: {reclamo_id}\n"
                         f"📊 Estado: Pendiente\n"
                         f"📝 Resumen: {texto}")
        else:
            respuesta = "❌ No pude registrar tu reclamo. ¿Intentamos de nuevo?"
        self.redis_client.hset(estado_clave, "fase", "inicio")
        return respuesta

    async def _process_consultar_reclamos(self, texto: str, estado: dict, estado_clave: str) -> str:
        if not re.match(r'^\d+$', texto):
            return "❓ Por favor, dame un ID de reclamo (solo números)."
        id_reclamo = int(texto)
        if not self.consulta_reclamo:
            return "❌ Funcionalidad no disponible: consultar_reclamo_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
        respuesta, codigo = self.consulta_reclamo.ejecutar(id_reclamo)
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
            direccion = f"calle {calle}, barrio {barrio}" if calle != 'No disponible' and barrio != 'No disponible' else (
                calle if calle != 'No disponible' else barrio)
            respuesta = (f"📋 Detalles del reclamo ID {id_reclamo}:\n"
                         f"📝 *Descripción*: {reclamo.get('DESCRIPCION', 'No disponible')}\n"
                         f"📊 *Estado*: {reclamo.get('ESTADO', 'No disponible')}\n"
                         f"📅 *Fecha de Reclamo*: {fecha_reclamo}\n"
                         f"👤 *Cliente*: {cliente.get('nombre', 'No disponible')} (DNI: {cliente.get('dni', 'No disponible')})\n"
                         f"🏠 *Dirección*: {direccion if direccion else 'No disponible'}")
            self.redis_client.hset(estado_clave, "fase", "inicio")
            return respuesta
        return "❌ No encontré ese reclamo. Intenta con otro ID para más detalles."

    async def _process_confirmar_actualizacion(self, texto: str, estado: dict, estado_clave: str) -> str:
        dni = estado.get("dni")
        campo = estado.get("campo_actualizar")
        if not self.actualizar:
            return "❌ Funcionalidad no disponible: actualizar_usuario_usecase no está configurado.\n\n🌟 ¿Necesitas algo más? Puedo ayudarte con un reclamo, actualizar datos, consultar estados o facturas."
        resultado, status = self.actualizar.ejecutar(dni, {campo: texto})
        if status == 200:
            nombre = estado.get('nombre', 'Usuario')
            respuesta = f"✅ ¡Actualización exitosa, {nombre}!\n✨ Tu {campo.lower()} ha sido actualizado a: {texto}."
        else:
            respuesta = "❌ No pude actualizar. ¿Probamos otra vez?"
        self.redis_client.hset(estado_clave, "fase", "inicio")
        return respuesta

    async def _format_reclamos(self, dni: str) -> str:
        if not self.consulta_estado:
            return "❌ Funcionalidad no disponible: consultar_estado_reclamo_usecase no está configurado."
        respuesta, codigo = self.consulta_estado.ejecutar(dni)
        if codigo == 200:
            if "mensaje" in respuesta:
                return f"ℹ️ {respuesta['mensaje']}"
            reclamos = respuesta.get("reclamos", [])
            if not reclamos:
                return "ℹ️ No tienes reclamos registrados recientemente."
            return "\n".join(
                [f"🆔 ID: {r['ID_RECLAMO']} | 📊 Estado: {r['ESTADO']} | 📝 Descripción: {r['DESCRIPCION'][:50]}..." for r
                 in reclamos])
        return "❌ No pude obtener tus reclamos. Intenta de nuevo."