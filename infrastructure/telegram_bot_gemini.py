#infraestructure/telegram_bot_gemini.py
from flask import Flask
from infrastructure.settings import TELEGRAM_BOT_TOKEN
from adapters.telegram_adapter_gemini import TelegramAdapterGemini
from application.otros_modelos.gemini_service import GeminiService
from application.otros_modelos.detectar_intencion_gemini_usecase import DetectarIntencionGeminiUseCase
from infrastructure.redis_client import RedisClient
from infrastructure.database import init_db
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
init_db(app)

if __name__ == "__main__":
    with app.app_context():
        logging.info("🚀 Iniciando bot de Telegram con Gemini...")

        # Inicializar cliente de Redis
        redis_client = RedisClient().get_client()

        # Inicializar servicio Gemini y usecase
        gemini_service = GeminiService(redis_client=redis_client)  # Pasamos redis_client aquí
        detectar_intencion_usecase = DetectarIntencionGeminiUseCase(gemini_service)

        # Los casos de uso de reclamos y consultas se instanciarán dentro del adapter si son None
        registrar_reclamo_usecase = None
        actualizar_usuario_usecase = None
        consultar_estado_reclamo_usecase = None
        consultar_reclamo_usecase = None

        # Inicializar y correr el bot con Gemini
        bot = TelegramAdapterGemini(
            TELEGRAM_BOT_TOKEN,
            detectar_intencion_usecase,
            registrar_reclamo_usecase,
            actualizar_usuario_usecase,
            consultar_estado_reclamo_usecase,
            consultar_reclamo_usecase,
            redis_client,
            app
        )
        bot.run()