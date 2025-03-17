#adapters/ telegram_adapter.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.detectar_intencion_usecase import DetectarIntencionUseCase
import re

# Estado de los usuarios
user_states = {}

class TelegramAdapter:
    def __init__(self, token, detectar_intencion_usecase: DetectarIntencionUseCase,
                 reclamo_usecase: RegistrarReclamoUseCase, actualizar_usecase: ActualizarUsuarioUseCase,
                 consulta_usecase: ConsultarEstadoReclamoUseCase):
        self.token = token
        self.detectar_intencion_usecase = detectar_intencion_usecase
        self.reclamo_usecase = reclamo_usecase
        self.actualizar_usecase = actualizar_usecase
        self.consulta_usecase = consulta_usecase
        self.app = ApplicationBuilder().token(self.token).build()

        self.setup_handlers()

    def setup_handlers(self):
        """Configura los comandos y mensajes del bot."""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mensaje de bienvenida."""
        await update.message.reply_text(
            "¡Hola! Soy el asistente virtual de DECSA. Puedes realizar reclamos, actualizar datos o consultar su estado. ¿En qué te ayudo?"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los mensajes del usuario y ejecuta las acciones correspondientes."""
        user_id = update.message.from_user.id
        texto_usuario = update.message.text.strip().lower()

        # 🔹 1️⃣ Detectar intención
        intencion = self.detectar_intencion_usecase.ejecutar(texto_usuario)

        # 🔹 2️⃣ Estado del usuario
        state = user_states.get(user_id, {"fase": "inicio"})

        if state["fase"] == "inicio":
            if intencion == "Reclamo":
                user_states[user_id] = {"fase": "pedir_dni", "accion": "reclamo"}
                await update.message.reply_text("Por favor, ingresa tu DNI para proceder con el reclamo.")
            elif intencion == "Actualizar":
                user_states[user_id] = {"fase": "pedir_dni", "accion": "actualizar"}
                await update.message.reply_text("Para actualizar tus datos, dime tu DNI.")
            elif intencion == "Consultar":
                user_states[user_id] = {"fase": "pedir_dni", "accion": "consultar"}
                await update.message.reply_text("Para consultar el estado de tu reclamo, ingresa tu DNI.")
            else:
                await update.message.reply_text("No entendí tu solicitud.")

        elif state["fase"] == "pedir_dni":
            if not re.match(r'^\d{7,8}$', texto_usuario):
                await update.message.reply_text("⚠️ El DNI ingresado no es válido. Asegúrate de ingresar solo números.")
                return

            user_states[user_id]["dni"] = texto_usuario
            await update.message.reply_text(f"¿Eres el usuario con DNI {texto_usuario}? Responde con 'Sí' o 'No'.")
            user_states[user_id]["fase"] = "confirmar_dni"

        elif state["fase"] == "confirmar_dni":
            if texto_usuario not in ["sí", "si", "no"]:
                await update.message.reply_text("Por favor, responde 'Sí' o 'No' para confirmar tu identidad.")
                return

            if texto_usuario == "no":
                user_states[user_id] = {"fase": "inicio"}
                await update.message.reply_text("Entiendo. Por favor, ingresa el DNI correcto.")
                return

            await update.message.reply_text("Gracias por confirmar. ¿Cuál es tu solicitud?")
            user_states[user_id]["fase"] = "ejecutar_accion"

        elif state["fase"] == "ejecutar_accion":
            dni = user_states[user_id]["dni"]
            accion = user_states[user_id]["accion"]

            try:
                if accion == "reclamo":
                    resultado = self.reclamo_usecase.ejecutar(dni, texto_usuario)
                elif accion == "actualizar":
                    resultado = self.actualizar_usecase.ejecutar(dni, {"valor": texto_usuario})
                elif accion == "consultar":
                    resultado = self.consulta_usecase.ejecutar(dni)
                else:
                    resultado = "Acción no válida."
            except Exception as e:
                resultado = f"❌ Error al procesar la solicitud: {str(e)}"

            await update.message.reply_text(resultado)
            user_states[user_id] = {"fase": "inicio"}

    def run(self):
        """Inicia el bot de Telegram."""
        print("🚀 Bot de Telegram corriendo...")
        self.app.run_polling()
