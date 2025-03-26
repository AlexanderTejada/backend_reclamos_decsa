import pyodbc

def test_connection(server, database, user, password, driver):
    connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password}"
    try:
        conn = pyodbc.connect(connection_string, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE();")
        result = cursor.fetchone()
        print(f"✅ Conexión exitosa a {database} ({server}) - Fecha del servidor: {result[0]}")
        conn.close()
    except Exception as e:
        print(f"❌ Error al conectar con {database} ({server}): {e}")

# DB1 - Solo lectura
test_connection(
    server="179.41.8.106,1433",
    database="PR_CAU",
    user="lectura",
    password="procoop",
    driver="ODBC Driver 17 for SQL Server"
)

# DB2 - Escritura
test_connection(
    server="168.226.219.57,2424",
    database="DECSA_EXC",
    user="sa",
    password="Excel159753",
    driver="ODBC Driver 17 for SQL Server"
)
