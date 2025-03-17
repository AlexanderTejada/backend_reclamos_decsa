import pyodbc

server = "(local)"  # O usa "." si no funciona
database = "dbEjemplo1"
driver = "{ODBC Driver 17 for SQL Server}"

try:
    conn = pyodbc.connect(f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes")
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 * FROM dbo.WS_USERS")  # Prueba una consulta
    row = cursor.fetchone()
    print("Conexión exitosa:", row)
except Exception as e:
    print("Error conectando a SQL Server:", e)
