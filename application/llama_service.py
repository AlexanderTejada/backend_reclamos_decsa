#application/ llama_services.py
import requests
import logging
from infrastructure.settings import Config

class LlamaService:
    def __init__(self):
        self.llama_url = Config.LLAMA_API_URL  # 🔹 URL del servidor de Llama 3

    def generar_respuesta(self, prompt):
        """Envía un prompt a Llama 3 y devuelve la respuesta generada."""
        payload = {"model": "llama3:latest", "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.llama_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get("response", "⚠️ Error en la respuesta de Llama.").strip()
        except requests.RequestException as e:
            logging.error(f"Error en la solicitud a Llama: {str(e)}")
            return "⚠️ No se pudo procesar la solicitud."

    def detectar_intencion(self, mensaje):
        """Usa Llama 3 para detectar la intención del mensaje del usuario."""
        prompt = f"""
        Un usuario escribió: "{mensaje}"

        Responde estrictamente con UNA SOLA palabra que indique la intención del usuario, usando SOLO estas opciones:
        - Reclamo
        - Actualizar
        - Consultar
        - Conversar

        Si el mensaje es solo un saludo, responde "Conversar".

        Ejemplos:
        "Hola" -> Conversar
        "Buenas tardes" -> Conversar
        "Quiero hacer un reclamo" -> Reclamo
        "Necesito actualizar mi celular" -> Actualizar
        "Quiero ver mis reclamos" -> Consultar
        """
        return self.generar_respuesta(prompt)

    def generar_resumen(self, historial):
        """Genera un resumen breve de la conversación."""
        prompt = f"""
        Basado en esta conversación, genera un resumen breve en SEGUNDA PERSONA. 

        - Usa frases directas como "Has realizado un reclamo" en lugar de "El usuario ha realizado un reclamo".
        - Si es un reclamo, di "Has registrado un reclamo con descripción: [descripción]".
        - Si es una consulta de estado, di "Has consultado el estado de tu reclamo".
        - Si es una actualización de datos, di "Has actualizado tu [dato] correctamente".
        - No incluyas detalles innecesarios, solo el resultado final.

        Conversación:
        {historial}

        Resumen:
        """
        return self.generar_respuesta(prompt)
