# test_connection.py
from sqlalchemy import create_engine, text
from test_settings import TestConfig

# Crear motores de conexión para db1 (PR_CAU)
engine_db1 = create_engine(TestConfig.SQLALCHEMY_BINDS['db1'])

# Conectar a db1
with engine_db1.connect() as connection:
    # Ejecutar la consulta
    query = """
    SELECT
        persona.COD_PER as IdPersona,
        persona.APELLIDOS as Nombre,
        persona.NUM_DNI as Dni,
        persona.OBSERVAC as Observaciones,
        factu.COD_SUM as CodigoSuministro,
        factu.NUM_COM as NumeroComprobante,
        factu.FECHA as FechaEmision,
        factu.PAGA as Estado,
        factu.TOTAL1,
        factu.VTO1,
        sumi.OBS_POS as ObservacionPostal,
        barrio.DES_BAR as Barrio,
        calle.DES_CAL as calle,
        ser.NUM_MED as NumeroMedidor,
        conser.PERIODO,
        conser.CONSUMO
    FROM PERSONAS as persona
    LEFT JOIN FACTURAS as factu ON persona.COD_PER = factu.COD_PER
    LEFT JOIN SUMSOC as sumi ON factu.COD_SUM = sumi.COD_SUM
    LEFT JOIN CONS_SER as conser ON conser.ID_FAC = factu.ID_FAC
    LEFT JOIN BARRIOS as barrio ON sumi.COD_BAR = barrio.COD_BAR
    LEFT JOIN CALLES as calle ON sumi.COD_CAL = calle.COD_CAL
    LEFT JOIN SERSOC as ser ON sumi.COD_SUM = ser.COD_SUM
    WHERE persona.APELLIDOS = :apellidos
    ORDER BY factu.ID_FAC DESC
    """
    result = connection.execute(text(query), {"apellidos": "AGUILAR CARMEN"}).fetchone()

    if result:
        print("Conexión exitosa. Datos traídos de db1 (PR_CAU):")
        print(f"IdPersona: {result.IdPersona}")
        print(f"Nombre: {result.Nombre}")
        print(f"DNI: {result.Dni}")
        print(f"Observaciones: {result.Observaciones}")
        print(f"CodigoSuministro: {result.CodigoSuministro}")
        print(f"NumeroComprobante: {result.NumeroComprobante}")
        print(f"FechaEmision: {result.FechaEmision}")
        print(f"Estado: {result.Estado}")
        print(f"Total: {result.TOTAL1}")
        print(f"Vencimiento: {result.VTO1}")
        print(f"ObservacionPostal: {result.ObservacionPostal}")
        print(f"Barrio: {result.Barrio}")
        print(f"Calle: {result.calle}")
        print(f"NumeroMedidor: {result.NumeroMedidor}")
        print(f"Periodo: {result.PERIODO}")
        print(f"Consumo: {result.CONSUMO}")
    else:
        print("No se encontraron datos en db1.")