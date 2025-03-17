import os
from dotenv import load_dotenv

load_dotenv()

print("Contraseña cargada:", os.getenv("DB_PASSWORD"))
