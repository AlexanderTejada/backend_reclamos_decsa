#application/ procesar_texto_con_llama_usecase.py
from infrastructure.settings import Config
import requests

class ProcesarTextoConLlamaUseCase:
    def __init__(self):
        self.llama_api_url = Config.LLAMA_API_URL

    def ejecutar(self, texto):
        try:
            respuesta = requests.post(self.llama_api_url, json={"texto": texto})
            return respuesta.json().get("respuesta", "Error en la respuesta")
        except Exception as e:
            return f"⚠️ Error al procesar con Llama: {str(e)}"
