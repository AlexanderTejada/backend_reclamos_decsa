# application/chatgpt_service.py
import logging
import time
from openai import OpenAI
from infrastructure.settings import Config
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatGPTService:
    def __init__(self, redis_client=None):
        self.client = OpenAI(api_key=Config.CHATGPT_API_KEY)
        self.redis_client = redis_client
        logging.info("ChatGPTService inicializado con API Key configurada.")

    def generar_respuesta(self, prompt, historial=""):
        try:
            if self.redis_client:
                cache_key = f"chatgpt:v1:{hash(prompt + historial)}"
                cached_response = self.redis_client.get(cache_key)
                if cached_response:
                    logging.info(f"Respuesta obtenida del caché: {cached_response}")
                    return cached_response.decode('utf-8')

            full_prompt = f"""
            Eres DECSA, un asistente virtual oficial de Distribuidora Eléctrica de Caucete S.A. Ayudas con:
            1) Reclamos sobre servicios eléctricos (ej: "quiero hacer un reclamo").
            2) Actualizar datos personales (ej: "actualizar mi celular").
            3) Consultar el estado de un reclamo (ej: "consultar estado").
            4) Consultar facturas (ej: "quiero ver mi factura" o "consultar factura").

            Normas:
            - En el primer mensaje (sin historial), preséntate y explica qué podés hacer.
            - No repitas la intro después, usá el historial para responder directo.
            - Respuestas cálidas y claras, adaptadas al usuario.
            - Detectá la intención (Reclamo, Actualizar, Consultar, ConsultarFacturas o Conversar).
            - Si es "Actualizar", pedí qué dato cambiar (calle, barrio, celular, correo).
            - Si es "ConsultarFacturas", pedí el DNI para buscar la información.
            - Devolvé JSON con "intencion" y "respuesta".

            Historial reciente (últimos 5 mensajes):
            {historial}

            Mensaje actual: "{prompt}"
            """

            start_time = time.time()
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # O "gpt-4" si tenés acceso
                messages=[
                    {"role": "system", "content": "Sos un asistente que responde en JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )

            texto_respuesta = response.choices[0].message.content.strip()
            first_chunk_time = time.time()
            logging.info(f"Tiempo de respuesta: {first_chunk_time - start_time:.2f} segundos")
            logging.info(f"Respuesta de ChatGPT: {texto_respuesta}")

            # Aseguramos que sea JSON válido
            try:
                json.loads(texto_respuesta)
            except json.JSONDecodeError:
                logging.warning(f"Respuesta no es JSON: {texto_respuesta}")
                texto_respuesta = '{"intencion": "Conversar", "respuesta": "No entendí bien. ¿En qué te ayudo? Decime si querés un reclamo, actualizar datos, consultar algo o ver tu factura."}'

            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, texto_respuesta)
                logging.info(f"Guardado en caché: {cache_key}")

            return texto_respuesta
        except Exception as e:
            logging.error(f"Error con ChatGPT: {str(e)}")
            return '{"intencion": "Conversar", "respuesta": "Ups, algo falló. ¿En qué te ayudo?"}'

    def detectar_intencion(self, mensaje, historial=""):
        logging.info(f"Enviando a ChatGPT: '{mensaje}'")
        return self.generar_respuesta(mensaje, historial)