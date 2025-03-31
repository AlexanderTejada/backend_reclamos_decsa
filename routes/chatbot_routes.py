# routes/chatbot_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from infrastructure.database import get_db
from infrastructure.security import get_current_user, require_role
from domain.entities import Usuario
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
router = APIRouter()

# Variable global para almacenar el detectar_intencion_usecase
_detectar_intencion_usecase = None

def set_detectar_intencion_usecase(usecase):
    global _detectar_intencion_usecase
    _detectar_intencion_usecase = usecase

def get_detectar_intencion_usecase():
    if _detectar_intencion_usecase is None:
        raise RuntimeError("DetectarIntencionUseCase not initialized.")
    return _detectar_intencion_usecase

class ChatRequest(BaseModel):
    message: str

@router.post("", response_model=dict)
async def chat_with_bot(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
    detectar_intencion_usecase=Depends(get_detectar_intencion_usecase)
):
    try:
        response = await detectar_intencion_usecase.ejecutar(request.message)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error al procesar la consulta del chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar la consulta")