import logging
import time
from openai import OpenAI
from infrastructure.settings import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DeepSeekService:
    def __init__(self, redis_client=None):
        self.client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        self.redis_client = redis_client
        logging.info("DeepSeekService inicializado con API Key y endpoint configurados.")

    def generar_respuesta(self, prompt):
        try:
            # Verificar caché
            if self.redis_client:
                cache_key = f"deepseek:v3:{hash(prompt)}"  # Usar hash para claves únicas
                cached_response = self.redis_client.get(cache_key)
                if cached_response:
                    logging.info(f"Respuesta obtenida del caché: {cached_response}")
                    return cached_response.decode('utf-8')

            # Generar respuesta con streaming
            start_time = time.time()
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system",
                     "content": "Eres DECSA. Responde en JSON con 'intencion' (Reclamo, Actualizar, Consultar, Conversar) y 'respuesta'."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=50,  # Reducido aún más
                stream=True
            )

            texto_respuesta = ""
            first_chunk_time = None
            http_ok_time = start_time  # Aproximamos el "200 OK" al inicio para este log
            for chunk in response:
                if chunk.choices[0].delta.content:
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        logging.info(
                            f"Tiempo desde inicio hasta primer fragmento: {first_chunk_time - start_time:.2f} segundos")
                        logging.info(
                            f"Tiempo desde HTTP 200 OK estimado hasta primer fragmento: {first_chunk_time - http_ok_time:.2f} segundos")
                    texto_respuesta += chunk.choices[0].delta.content
                    logging.info(f"Fragmento recibido: {chunk.choices[0].delta.content}")

            total_time = time.time() - start_time
            logging.info(f"Tiempo total de generación (streaming): {total_time:.2f} segundos")

            # Limpiar formato
            texto_respuesta = texto_respuesta.strip()
            if texto_respuesta.startswith("```json"):
                texto_respuesta = texto_respuesta.replace("```json", "").replace("```", "").strip()
            elif texto_respuesta.startswith("json"):
                texto_respuesta = texto_respuesta[4:].strip()
            logging.info(f"Respuesta completa de DeepSeek: {texto_respuesta}")

            # Guardar en caché
            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, texto_respuesta)
                logging.info(f"Respuesta guardada en caché con clave: {cache_key}")

            return texto_respuesta
        except Exception as e:
            logging.error(f"Error al contactar DeepSeek: {str(e)}")
            return '{"intencion": "Conversar", "respuesta": "Lo siento, hubo un problema al conectarme."}'

    def detectar_intencion(self, mensaje, historial=""):
        prompt = f"Mensaje: '{mensaje}'"  # Sin historial para máxima velocidad
        logging.info(f"Prompt enviado a DeepSeek: {prompt}")
        return self.generar_respuesta(prompt)