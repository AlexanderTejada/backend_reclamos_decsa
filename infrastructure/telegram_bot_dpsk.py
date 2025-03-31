from flask import Flask
from infrastructure.settings import TELEGRAM_BOT_TOKEN
from adapters.telegram_adapter_dpsk import TelegramAdapterDPSK
from application.otros_modelos.deepseek_service import DeepSeekService
from application.otros_modelos.detectar_intencion_deepseek_usecase import DetectarIntencionDeepSeekUseCase
from infrastructure.redis_client import RedisClient
from infrastructure.database import init_db
import logging

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
init_db(app)

if __name__ == "__main__":
    with app.app_context():
        logging.info("🚀 Iniciando bot de Telegram con DeepSeek...")

        # Inicializar cliente de Redis
        redis_client = RedisClient().get_client()

        # Inicializar servicio DeepSeek y usecase
        deepseek_service = DeepSeekService()
        detectar_intencion_usecase = DetectarIntencionDeepSeekUseCase(deepseek_service)

        # Los casos de uso de reclamos y consultas se instanciarán dentro del adapter si son None
        registrar_reclamo_usecase = None
        actualizar_usuario_usecase = None
        consultar_estado_reclamo_usecase = None
        consultar_reclamo_usecase = None

        # Inicializar y correr el bot con DeepSeek
        bot = TelegramAdapterDPSK(
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
