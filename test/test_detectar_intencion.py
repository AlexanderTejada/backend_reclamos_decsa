import re
import requests
import redis
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from collections import defaultdict


# Configuración
TELEGRAM_BOT_TOKEN = "7947217030:AAFX-Fj8Z_7QM_TMYi7J5YuKCM2n9rV7UbM"
LLAMA_API_URL = "http://localhost:11434/api/generate"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

class LlamaService:
    def __init__(self):
        self.llama_url = LLAMA_API_URL

    def generar_respuesta(self, mensaje, historial):
        prompt = f"""
        Eres un asistente virtual oficial de DECSA. Ayudas a los usuarios a:
        1) Realizar reclamos.
        2) Actualizar datos (teléfono, correo electrónico, dirección).
        3) Consultar el estado de un reclamo.

        Usa el historial reciente de la conversación para recordar detalles previos y responder con coherencia. Si el usuario ya mencionó su nombre o información, utilízala en las respuestas. No repitas saludos si ya los has hecho. Si la conversación es nueva (no hay historial), saluda cordialmente.

        Si el usuario pregunta: "¿Cómo hago un reclamo?" o "¿Cómo actualizo mis datos?" o variantes, indícale que debe escribir frases como "quiero hacer un reclamo", "actualizar mi dirección", "actualizar mi correo" o "consultar el estado de mi reclamo", y que el bot le guiará paso a paso.

        Si el usuario expresa frustración o queja, responde empáticamente y sugiere escribir "quiero hacer un reclamo" para registrar su inconveniente.

        Historial reciente:
        {historial}

        Mensaje actual del usuario: "{mensaje}"
        """

        payload = {
            "model": "llama3:latest",
            "prompt": prompt.strip(),
            "stream": False,
            "options": {"temperature": 0.6}
        }
        try:
            response = requests.post(self.llama_url, json=payload, timeout=100)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"❌ Error al contactar Llama: {e}")
            return "Disculpa, hubo un problema al procesar tu mensaje. ¿Podrías repetirlo?"

class DecsaBot:
    def __init__(self, token):
        self.llama_service = LlamaService()
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        self.app = ApplicationBuilder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("reset", self.reset_historial))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await self.reset_historial_manual(user_id)
        await update.message.reply_text("¡Hola! Soy el asistente virtual de DECSA. ¿En qué puedo ayudarte hoy?")

    async def reset_historial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await self.reset_historial_manual(user_id)
        await update.message.reply_text("Memoria de la conversación reiniciada. Empecemos de nuevo. ¿En qué puedo ayudarte?")

    async def reset_historial_manual(self, user_id):
        self.redis_client.delete(f"user:{user_id}:historial")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        mensaje = update.message.text.strip()

        historial_clave = f"user:{user_id}:historial"
        self.redis_client.rpush(historial_clave, f"Usuario: {mensaje}")

        historial = " | ".join(self.redis_client.lrange(historial_clave, -10, -1))

        respuesta_llama = self.llama_service.generar_respuesta(mensaje, historial)

        respuesta = respuesta_llama or "¡Perdón! No entendí bien. Por favor, reformula tu pregunta o indícame en qué puedo ayudarte."

        self.redis_client.rpush(historial_clave, f"Bot: {respuesta}")

        await update.message.reply_text(respuesta)

    def run(self):
        print("🚀 Bot DECSA corriendo con Llama, Redis y respuestas guiadas adaptativas...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = DecsaBot(TELEGRAM_BOT_TOKEN)
    bot.run()

