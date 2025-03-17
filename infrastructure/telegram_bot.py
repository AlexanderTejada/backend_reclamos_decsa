from infrastructure.settings import TELEGRAM_BOT_TOKEN
from adapters.telegram_adapter import TelegramAdapter
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.actualizar_usuario_usecase import ActualizarUsuarioUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from infrastructure.database import db_session

# 🔹 Inicializamos los repositorios
user_repository = SQLAlchemyUsuarioRepository(db_session)
reclamo_repository = SQLAlchemyReclamoRepository(db_session)

# 🔹 Inicializamos los casos de uso
registrar_reclamo_usecase = RegistrarReclamoUseCase(reclamo_repository, user_repository)
actualizar_usuario_usecase = ActualizarUsuarioUseCase(user_repository)
consultar_estado_reclamo_usecase = ConsultarEstadoReclamoUseCase(reclamo_repository, user_repository)

# 🔹 Inicializamos el bot con los casos de uso
bot = TelegramAdapter(
    TELEGRAM_BOT_TOKEN,
    registrar_reclamo_usecase,
    actualizar_usuario_usecase,
    consultar_estado_reclamo_usecase
)

if __name__ == "__main__":
    bot.run()
