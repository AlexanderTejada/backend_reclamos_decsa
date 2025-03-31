import requests
import logging
import json
from infrastructure.settings import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class LlamaService:
    def __init__(self):
        self.llama_url = Config.LLAMA_API_URL
        logging.info(f"Inicializando LlamaService con URL: {self.llama_url}")

    def generar_respuesta(self, prompt):
        payload = {
            "model": "llama3:latest",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.5}
        }
        logging.info(f"Enviando solicitud a Llama con payload: {payload}")
        try:
            response = requests.post(self.llama_url, json=payload, timeout=500)
            response.raise_for_status()
            respuesta_json = response.json()
            logging.info(f"Respuesta cruda de Llama: {respuesta_json}")
            return respuesta_json.get("response", "").strip()
        except requests.RequestException as e:
            logging.error(f"Error al contactar Llama: {str(e)}")
            return '{"intencion": "Conversar", "respuesta": "Lo siento, hubo un problema. Te sugiero hacer un reclamo, actualizar datos o consultar un estado."}'

    def detectar_intencion(self, mensaje, historial=""):
        prompt = f"""
        Eres DECSA, un asistente virtual oficial de DECSA. Tu objetivo principal es asistir a los usuarios con:
        1) Hacer reclamos relacionados con servicios de DECSA (ej. "quiero hacer un reclamo", "no tengo luz", "el otro día cayó un poste").
        2) Actualizar datos personales (ej. "quiero actualizar mi dirección", "cambiar teléfono").
        3) Consultar el estado de un reclamo (ej. "consultar estado", "cómo está mi reclamo").

        Usa el historial para responder de manera coherente y útil. Si detectas una intención clara relacionada con las funciones de DECSA, clasifícala y da una breve confirmación. Si el mensaje no parece estar relacionado con reclamos, actualizaciones o consultas (por ejemplo, comentarios personales inapropiados o fuera de contexto como 'tengo el pene torcido'), clasifícalo como 'Conversar' y responde con empatía genérica sin profundizar, reorientando al usuario. Si no hay intención clara ("Conversar"), genera una respuesta natural y detallada basada en el mensaje y el historial, recordando datos específicos (como nombres de perros o gatos) y respondiendo preguntas contextuales como '¿cómo se llama mi perro?' con información del historial. Si el usuario repite la misma pregunta, ofrece una respuesta variada y útil. Siempre termina las respuestas conversacionales con una sugerencia clara y directa para que el usuario haga un reclamo, actualice datos o consulte un estado, reorientándolo a las funciones principales de DECSA.

        Historial reciente (últimos 5 mensajes):
        {historial}

        Mensaje actual: "{mensaje}"

        Responde en formato JSON con:
        - "intencion": "Reclamo", "Actualizar", "Consultar" o "Conversar".
        - "respuesta": Una breve confirmación para intenciones claras (ej. "Intención: Actualizar") o una respuesta conversacional para "Conversar".
        """
        logging.info(f"Prompt enviado a Llama: {prompt}")
        return self.generar_respuesta(prompt)