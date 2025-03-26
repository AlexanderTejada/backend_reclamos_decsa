# test_settings.py

# Configuración de SQL Server (base de datos real)
SQL_SERVER = "179.41.8.106,1433"  # Servidor real
SQL_DATABASE = "PR_CAU"  # Base de datos real
SQL_USER = "lectura"
SQL_PASSWORD = "procoop"
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

# URI de conexión para la base de datos real (db1, solo lectura)
DB_URI1 = f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER}/{SQL_DATABASE}?driver={SQL_DRIVER}"

# URI de conexión para la base de datos secundaria (db2, lectura/escritura)
# Usaremos SQLite para pruebas
DB_URI2 = "sqlite:///test_decsa_db2.sqlite"  # Base de datos local para pruebas

# Configuración de SQLAlchemy
class TestConfig:
    SQLALCHEMY_DATABASE_URI = DB_URI2  # Usamos db2 por defecto para escritura
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Múltiples bases de datos
    SQLALCHEMY_BINDS = {
        "db1": DB_URI1,  # Base de datos real (solo lectura)
        "db2": DB_URI2,  # Base de datos secundaria (lectura/escritura)
    }