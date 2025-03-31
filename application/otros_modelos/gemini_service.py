# application/gemini_service.py
import logging
import time
import google.generativeai as genai
from infrastructure.settings import Config
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GeminiService:
    def __init__(self, redis_client=None):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.redis_client = redis_client
        logging.info("GeminiService inicializado con API Key configurada.")

    def generar_respuesta(self, prompt, historial=""):
        try:
            if self.redis_client:
                cache_key = f"gemini:v1:{hash(prompt + historial)}"
                cached_response = self.redis_client.get(cache_key)
                if cached_response:
                    logging.info(f"Respuesta obtenida del caché: {cached_response}")
                    return cached_response.decode('utf-8')

            full_prompt = f"""
            Eres DECSA, un asistente virtual oficial de Distribuidora Eléctrica de Caucete S.A. (DECSA). Tu función es ayudar a los usuarios con:
                cvgcv
            1) Hacer reclamos sobre servicios eléctricos (ejemplo: "quiero hacer un reclamo", "no tengo luz").
            2) Actualizar datos personales (ejemplo: "quiero actualizar mi dirección", "cambiar mi celular").
            3) Consultar el estado de un reclamo (ejemplo: "consultar estado", "¿cómo está mi reclamo?").

            Normas de interacción:
            - En el primer mensaje (sin historial), preséntate como DECSA y explica amablemente en qué puedes ayudar.
            - No repitas la presentación en cada respuesta; usa el historial para mantener continuidad y responder directamente.
            - Genera respuestas cálidas, empáticas y adaptadas al tono o contexto del mensaje del usuario.
            - Detecta la intención del usuario (Reclamo, Actualizar, Consultar o Conversar) y confirma la intención con una respuesta humana y cercana.
            - Si la intención es "Actualizar", no asumas un campo específico (como "CALLE" para "dirección"); en cambio, pide al usuario que especifique qué dato quiere cambiar (calle, barrio, celular o correo).
            - Incluye una instrucción clara sobre qué debe escribir el usuario para avanzar. Para "Reclamo" o "Consultar", pide el DNI. Para "Actualizar", pide elegir entre 'calle', 'barrio', 'celular' o 'correo'.
            - NO menciones 'cancelar' o 'salir' como opciones; esto se manejará fuera de esta respuesta.

            Historial reciente (últimos 5 mensajes):
            {historial}

            Mensaje actual: "{prompt}"

            Responde en formato JSON con:
            - "intencion": "Reclamo", "Actualizar", "Consultar" o "Conversar".
            - "respuesta": Una respuesta cálida, empática y adaptada al mensaje, con una instrucción clara para proceder (ejemplo: "dame tu DNI" para Reclamo/Consultar, "dime qué dato quieres actualizar: calle, barrio, celular o correo" para Actualizar).
            """

            start_time = time.time()
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 500,
                }
            )

            texto_respuesta = response.text.strip()
            first_chunk_time = time.time()
            logging.info(f"Tiempo desde inicio hasta respuesta: {first_chunk_time - start_time:.2f} segundos")
            logging.info(f"Respuesta completa de Gemini: {texto_respuesta}")

            if texto_respuesta.startswith("```json"):
                texto_respuesta = texto_respuesta.replace("```json", "").replace("```", "").strip()
            elif texto_respuesta.startswith("json"):
                texto_respuesta = texto_respuesta[4:].strip()

            try:
                json.loads(texto_respuesta)
            except json.JSONDecodeError:
                logging.warning(f"Respuesta incompleta o inválida: {texto_respuesta}")
                texto_respuesta = '{"intencion": "Conversar", "respuesta": "No entendí bien tu mensaje. ¿En qué puedo ayudarte hoy? Puedes decirme si quieres hacer un reclamo, actualizar datos o consultar algo."}'

            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, texto_respuesta)
                logging.info(f"Respuesta guardada en caché con clave: {cache_key}")

            return texto_respuesta
        except Exception as e:
            logging.error(f"Error al contactar Gemini: {str(e)}")
            return '{"intencion": "Conversar", "respuesta": "Lo siento, hubo un problema al procesar tu mensaje. ¿En qué puedo ayudarte?"}'

    def detectar_intencion(self, mensaje, historial=""):
        prompt = f"Mensaje: '{mensaje}'"
        logging.info(f"Prompt enviado a Gemini: {prompt}")
        return self.generar_respuesta(mensaje, historial)