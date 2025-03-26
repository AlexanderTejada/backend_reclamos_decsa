# infrastructure/extensions.py
from fastapi.middleware.cors import CORSMiddleware

def init_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5174", "http://localhost:5173"],  # Permitir ambos puertos por si cambias
        allow_credentials=True,
        allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, etc.)
        allow_headers=["*"],  # Permitir todos los headers
    )