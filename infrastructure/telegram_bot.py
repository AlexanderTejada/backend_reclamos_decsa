from flask import Flask
from infrastructure.settings import Config, TELEGRAM_BOT_TOKEN
from adapters.telegram_adapter import TelegramAdapter
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
from application.detectar_intencion_usecase import DetectarIntencionUseCase
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.database import init_db, db_session, get_db_session
from application.llama_service import LlamaService
from infrastructure.redis_client import RedisClient
import logging

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
init_db(app)

if __name__ == "__main__":
    with app.app_context():
        logging.info("🚀 Iniciando bot de Telegram...")

        # Usar db_session (vinculada a db2) y crear una sesión para db1 si es necesario
        # No es necesario aquí, ya que lo manejará el adapter
        # Inicializar repositorios y casos de uso no es necesario aquí, se hará en el adapter

        # Inicializar cliente de Redis
        redis_client = RedisClient().get_client()

        # Inicializar servicios de IA
        llama_service = LlamaService()
        detectar_intencion_usecase = DetectarIntencionUseCase(llama_service)

        # Inicializar casos de uso (pueden ser nulos inicialmente, se crean en el adapter)
        registrar_reclamo_usecase = None
        actualizar_usuario_usecase = None
        consultar_estado_reclamo_usecase = None
        consultar_reclamo_usecase = None

        # Inicializar el bot, pasando la aplicación
        bot = TelegramAdapter(
            TELEGRAM_BOT_TOKEN,
            detectar_intencion_usecase,
            registrar_reclamo_usecase,
            actualizar_usuario_usecase,
            consultar_estado_reclamo_usecase,
            consultar_reclamo_usecase,
            redis_client,
            app  # Añadido el argumento 'app'
        )
        bot.run()