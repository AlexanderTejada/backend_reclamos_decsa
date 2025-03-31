# chattigo_app.py
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from infrastructure.settings import Config
from infrastructure.extensions import init_cors
from infrastructure.database import init_db, get_db_session, get_db
from infrastructure.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infrastructure.sqlalchemy_reclamo_repository import SQLAlchemyReclamoRepository
from application.registrar_reclamo_usecase import RegistrarReclamoUseCase
from application.consultar_estado_reclamo_usecase import ConsultarEstadoReclamoUseCase
from application.consultar_reclamo_usecase import ConsultarReclamoUseCase
from routes.user_routes import cliente_router as user_router, init_cliente_services, get_actualizar_cliente_usecase
from routes.reclamo_routes import reclamo_router, init_reclamo_services
from routes.factura_routes import factura_router, init_factura_services, get_consultar_facturas_usecase
from routes.autenticacion_routes import router as usuario_router
from routes.roles_routes import router as rol_router
from routes.chatbot_routes import router as chatbot_router, set_detectar_intencion_usecase
from adapters.chattigo_adapter import ChattigoAdapter, ChattigoMessage, ChattigoResponse
from infrastructure.redis_client import RedisClient
from infrastructure.payload_handler import PayloadHandler
from application.chatgpt_service import ChatGPTService
from application.detectar_intencion_chatgpt_usecase import DetectarIntencionChatGPTUseCase
import logging
import os
import json
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_app():
    app = FastAPI(
        title="DECSA API",
        description="API para gestión de reclamos, facturas, usuarios y chatbot Chattigo",
        version="1.0.0"
    )
    app.config = Config

    init_db(app)
    init_cors(app)
    redis_client = RedisClient().get_client()

    app.include_router(user_router, prefix="/api/usuarios")
    app.include_router(reclamo_router, prefix="/api/reclamos")
    app.include_router(factura_router, prefix="/api/facturas")
    app.include_router(usuario_router, prefix="/api/admin/usuarios", tags=["Usuarios"])
    app.include_router(rol_router, prefix="/api/admin/roles", tags=["Roles"])
    app.include_router(chatbot_router, prefix="/api/chattigo", tags=["Chattigo"])

    init_cliente_services(app)
    init_reclamo_services(app)
    init_factura_services(app)

    chatgpt_service = ChatGPTService(redis_client=redis_client)
    detectar_intencion_usecase = DetectarIntencionChatGPTUseCase(chatgpt_service)
    app.detectar_intencion_usecase = detectar_intencion_usecase

    set_detectar_intencion_usecase(detectar_intencion_usecase)

    actualizar_cliente_usecase = get_actualizar_cliente_usecase()
    consultar_facturas_usecase = get_consultar_facturas_usecase()

    # Inicializar los repositorios y casos de uso para el ChattigoAdapter
    session_db1 = get_db_session(app, bind='db1')
    session_db2 = get_db_session(app, bind='db2')
    usuario_repository = SQLAlchemyUsuarioRepository(session_db1, session_db2)
    reclamo_repository = SQLAlchemyReclamoRepository(session_db2)

    registrar_reclamo_usecase = RegistrarReclamoUseCase(reclamo_repository, usuario_repository)
    consultar_estado_usecase = ConsultarEstadoReclamoUseCase(reclamo_repository, usuario_repository)
    consultar_reclamo_usecase = ConsultarReclamoUseCase(reclamo_repository)

    adapter = ChattigoAdapter(
        app.detectar_intencion_usecase,
        registrar_reclamo_usecase,
        actualizar_cliente_usecase,
        consultar_estado_usecase,
        consultar_reclamo_usecase,
        consultar_facturas_usecase,
        redis_client
    )

    # Endpoint para Chattigo
    @app.post("/webhook/chattigo", response_model=ChattigoResponse)
    async def webhook_chattigo(request: Request):
        return await adapter.handle_message(request)

    # Endpoint para WhatsApp
    @app.get("/webhook/whatsapp")
    async def verify_webhook(request: Request):
        query = request.query_params
        mode = query.get("hub.mode")
        token = query.get("hub.verify_token")
        challenge = query.get("hub.challenge")
        verify_token = os.getenv("VERIFY_TOKEN", "mi_token_secreto")
        logging.info(
            f"Recibida solicitud GET para verificar webhook: mode={mode}, token={token}, challenge={challenge}")
        if mode == "subscribe" and token == verify_token:
            logging.info("Webhook verificado con éxito")
            return int(challenge)
        logging.warning(f"Verificación fallida: mode={mode}, token recibido={token}, token esperado={verify_token}")
        raise HTTPException(status_code=403, detail="Verificación fallida")

    @app.post("/webhook/whatsapp")
    async def whatsapp_webhook(request: Request):
        try:
            # Leer el cuerpo de la solicitud como texto para depuración
            body = await request.body()
            logging.info(f"Cuerpo de la solicitud recibido: {body.decode('utf-8')}")

            # Intentar parsear el JSON
            try:
                parsed_payload = await PayloadHandler.parse_whatsapp_payload(request)
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear el JSON de la solicitud: {str(e)}")
                raise HTTPException(status_code=400, detail="Cuerpo de la solicitud no es un JSON válido")

            # Si parsed_payload es None, es una notificación de estado y no requiere procesamiento
            if parsed_payload is None:
                return {"status": "ok", "message": "Notificación de estado recibida"}

            class FakeRequest(Request):
                def __init__(self, payload: Dict):
                    super().__init__(scope={"type": "http"})
                    self._json = payload

                async def json(self):
                    return self._json

            fake_request = FakeRequest({
                "user_id": parsed_payload["user_id"],
                "message": parsed_payload["message"]
            })
            response = await adapter.handle_message(fake_request)
            await PayloadHandler.send_response("whatsapp", parsed_payload["user_id"], response["response"],
                                               extra_data=parsed_payload)
            return {"status": "ok"}
        except HTTPException as he:
            raise he
        except Exception as e:
            logging.error(f"Error en whatsapp_webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    return app


if __name__ == "__main__":
    try:
        app = create_app()
        host = os.getenv("FASTAPI_HOST", "0.0.0.0")
        port = int(os.getenv("FASTAPI_PORT", 5000))
        logging.info(f"✅ Servidor FastAPI iniciado en {host}:{port}")
        import uvicorn

        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logging.error(f"❌ Error al iniciar la aplicación: {str(e)}")
        raise