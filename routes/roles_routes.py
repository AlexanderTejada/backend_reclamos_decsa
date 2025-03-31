# routes/roles_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from infrastructure.database import get_db
from infrastructure.rol_repository import SQLAlchemyROLES  # Aseguro que el import sea correcto
from infrastructure.security import get_current_user, require_role
from domain.entities import Usuario
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
router = APIRouter()

class RolCreate(BaseModel):
    Nombre: str
    Descripcion: str | None = None
    OperadorCrea: str

class RolUpdate(BaseModel):
    Nombre: str | None = None
    Descripcion: str | None = None
    OperadorModifica: str | None = None

class RolDelete(BaseModel):
    OperadorAnula: str

class RolResponse(BaseModel):
    IdRol: int
    Nombre: str
    Descripcion: str | None
    Anulado: bool

@router.post("", response_model=RolResponse)
async def crear_rol(
    rol_data: RolCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    rol_service = SQLAlchemyROLES(db)
    try:
        nuevo_rol = rol_service.create_rol(
            rol_data.Nombre,
            rol_data.Descripcion,
            rol_data.OperadorCrea
        )
        return nuevo_rol.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id_rol}", response_model=RolResponse)
async def obtener_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    rol_service = SQLAlchemyROLES(db)
    rol = rol_service.get_rol_by_id(id_rol)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    return rol.to_dict()

@router.get("", response_model=list[RolResponse])
async def obtener_todos_roles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    rol_service = SQLAlchemyROLES(db)
    roles = rol_service.get_all_roles()
    return [rol.to_dict() for rol in roles]

@router.put("/{id_rol}", response_model=RolResponse)
async def actualizar_rol(
    id_rol: int,
    rol_data: RolUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    rol_service = SQLAlchemyROLES(db)
    rol_actualizado = rol_service.update_rol(
        id_rol,
        rol_data.Nombre,
        rol_data.Descripcion,
        rol_data.OperadorModifica
    )
    if not rol_actualizado:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    return rol_actualizado.to_dict()

@router.delete("/{id_rol}")
async def anular_rol(
    id_rol: int,
    rol_data: RolDelete,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    rol_service = SQLAlchemyROLES(db)
    rol_anulado = rol_service.delete_rol(
        id_rol,
        rol_data.OperadorAnula
    )
    if not rol_anulado:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    return {"message": "Rol anulado exitosamente."}