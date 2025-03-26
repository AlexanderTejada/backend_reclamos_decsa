# application/consultar_facturas_usecase.py
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ConsultarFacturasUseCase:
    def __init__(self, usuario_repository):
        """
        Inicializa el caso de uso con un repositorio de usuarios.

        Args:
            usuario_repository: Repositorio que proporciona acceso a los datos de usuarios y facturas.
        """
        self.usuario_repository = usuario_repository

    def ejecutar(self, dni: str):
        """
        Ejecuta la consulta de facturas para un usuario dado su DNI.

        Args:
            dni (str): Número de DNI del usuario.

        Returns:
            tuple: (respuesta, código de estado HTTP)
                - respuesta: Diccionario con la información de la factura o un mensaje de error.
                - código: 200 si éxito, 404 si no se encuentra, 500 si hay error.
        """
        try:
            # Obtener datos del usuario desde PR_CAU
            datos = self.usuario_repository.obtener_de_db1(dni)
            if not datos:
                logging.warning(f"No se encontraron datos para el DNI {dni} en PR_CAU")
                return {"mensaje": "No se encontraron datos para ese DNI"}, 404

            # Formatear la información de la factura
            factura_info = {
                "Nombre": f"{datos['Apellido']} {datos['Nombre']}",
                "DNI": datos["Dni"],
                "CodigoSuministro": datos["CodigoSuministro"] if datos["CodigoSuministro"] else "No disponible",
                "NumeroComprobante": datos["NumeroComprobante"] if datos["NumeroComprobante"] else "No disponible",
                "FechaEmision": (datos["FechaEmision"].strftime("%d/%m/%Y")
                                 if datos["FechaEmision"] and isinstance(datos["FechaEmision"], datetime)
                                 else "No disponible"),
                "Estado": "Pagada" if datos["EstadoFactura"] == "S" else "Pendiente" if datos[
                                                                                            "EstadoFactura"] == "N" else "No disponible",
                "Total": float(datos["TotalFactura"]) if datos["TotalFactura"] is not None else 0.0,
                "Vencimiento": (datos["VencimientoFactura"].strftime("%d/%m/%Y")
                                if datos["VencimientoFactura"] and isinstance(datos["VencimientoFactura"], datetime)
                                else "No disponible"),
                "ObservacionPostal": datos["ObservacionPostal"] if datos["ObservacionPostal"] else "No disponible",
                "Barrio": datos["Barrio"] if datos["Barrio"] else "No disponible",
                "Calle": datos["Calle"] if datos["Calle"] else "No disponible",
                "NumeroMedidor": datos["NumeroMedidor"] if datos["NumeroMedidor"] else "No disponible",
                "Periodo": datos["Periodo"] if datos["Periodo"] else "No disponible",
                "Consumo": float(datos["Consumo"]) if datos["Consumo"] is not None else 0.0
            }

            logging.info(f"Factura encontrada para el DNI {dni}")
            return {"factura": factura_info}, 200

        except Exception as e:
            logging.error(f"Error al consultar factura para el DNI {dni}: {str(e)}")
            return {"error": "Error al consultar la factura", "detalle": str(e)}, 500