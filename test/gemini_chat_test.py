import logging
import time
import google.generativeai as genai
from infrastructure.redis_client import RedisClient

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class GeminiTest:
    def __init__(self):
        try:
            # Configurar la API key directamente en el código
            self.api_key = "AIzaSyDxJGK-pAU_eIgtTwL-iCOKqtqSsSHZT1c"  # Reemplaza con tu clave de Gemini
            if not self.api_key or self.api_key == "tu-api-key-aqui":
                raise ValueError("API Key de Gemini no configurada. Reemplaza 'tu-api-key-aqui' con tu clave.")
            genai.configure(api_key=self.api_key)
            logging.info("API Key de Gemini configurada correctamente.")

            # Configuración del modelo
            generation_config = {
                "temperature": 0.2,  # Ligeramente más alto para respuestas elaboradas pero aún coherentes
                "top_p": 0.8,  # Reducido para mayor control, pero manteniendo variedad
                "top_k": 40,  # Aumentado para dar más opciones y riqueza en las respuestas
                "max_output_tokens": 500,  # Mucho más alto para respuestas detalladas
                "response_mime_type": "text/plain",
            }

            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",  # Versión gratuita
                generation_config=generation_config,
            )
            self.chat_session = self.model.start_chat(history=[])
            logging.info("Modelo Gemini inicializado correctamente.")

            # Configurar Redis
            try:
                self.redis_client = RedisClient().get_client()
                self.user_id = "test_user"  # ID de usuario para pruebas
                # Probar conexión a Redis
                self.redis_client.ping()
                logging.info("Conexión a Redis establecida correctamente.")
                # Limpiar historial previo para pruebas
                historial_key = f"chat:historial:{self.user_id}"
                self.redis_client.delete(historial_key)
                logging.info(f"Historial previo en Redis limpiado: {historial_key}")
            except Exception as e:
                logging.error(f"Error al conectar con Redis: {str(e)}")
                self.redis_client = None  # Continuar sin Redis si falla

        except Exception as e:
            logging.error(f"Error al inicializar GeminiTest: {str(e)}")
            raise

    def get_historial(self):
        """Obtiene el historial de Redis para el usuario."""
        if not self.redis_client:
            logging.warning("Redis no disponible, usando historial vacío.")
            return []
        try:
            historial_key = f"chat:historial:{self.user_id}"
            historial = self.redis_client.lrange(historial_key, -5, -1)  # Últimos 5 mensajes
            logging.info(f"Historial recuperado de Redis: {historial}")
            return historial if historial else []
        except Exception as e:
            logging.error(f"Error al obtener historial de Redis: {str(e)}")
            return []

    def save_historial(self, mensaje, respuesta):
        """Guarda el mensaje y la respuesta en Redis."""
        if not self.redis_client:
            logging.warning("Redis no disponible, no se guardará el historial.")
            return
        try:
            historial_key = f"chat:historial:{self.user_id}"
            self.redis_client.rpush(historial_key, f"Usuario: {mensaje}")
            self.redis_client.rpush(historial_key, f"DECSA: {respuesta}")
            # Mantener solo los últimos 10 mensajes (5 pares)
            self.redis_client.ltrim(historial_key, -10, -1)
            logging.info(f"Historial guardado en Redis: {historial_key}")
        except Exception as e:
            logging.error(f"Error al guardar historial en Redis: {str(e)}")

    def generar_respuesta(self, mensaje):
        try:
            # Obtener historial desde Redis
            historial = self.get_historial()
            historial_str = " | ".join(historial) if historial else ""

            # Crear prompt estructurado
            prompt = f"""
            Eres DECSA, un asistente virtual oficial de DECSA. Tu objetivo principal es asistir a los usuarios con:
            1) Hacer reclamos relacionados con servicios de DECSA (ej. "quiero hacer un reclamo", "no tengo luz").
            2) Actualizar datos personales (ej. "quiero actualizar mi dirección", "cambiar teléfono").
            3) Consultar el estado de un reclamo (ej. "consultar estado", "cómo está mi reclamo").

            Usa el historial para responder de manera coherente y útil. Si detectas una intención clara relacionada con las funciones de DECSA, clasifícala y da una breve confirmación. Si el mensaje no parece estar relacionado con reclamos, actualizaciones o consultas, clasifícalo como 'Conversar' y responde con empatía genérica, reorientando al usuario. Siempre termina las respuestas conversacionales con una sugerencia clara para que el usuario haga un reclamo, actualice datos o consulte un estado. Si el usuario pregunta por información específica (como un conteo o datos del historial), responde de manera directa y precisa.

            Historial reciente (últimos 5 mensajes):
            {historial_str}

            Mensaje actual: "{mensaje}"

            Responde en formato JSON con:
            - "intencion": "Reclamo", "Actualizar", "Consultar" o "Conversar".
            - "respuesta": Una breve confirmación o respuesta conversacional.
            """
            logging.info(f"Prompt enviado a Gemini: {prompt}")
            start_time = time.time()

            # Enviar mensaje y medir tiempo
            response = self.model.generate_content(prompt)
            response_time = time.time()
            logging.info(f"Tiempo hasta respuesta recibida: {response_time - start_time:.2f} segundos")

            # Obtener respuesta completa
            respuesta = response.text.strip()
            if respuesta.startswith("```json"):
                respuesta = respuesta.replace("```json", "").replace("```", "").strip()
            elif respuesta.startswith("json"):
                respuesta = respuesta[4:].strip()

            total_time = time.time() - start_time
            logging.info(f"Tiempo total de generación: {total_time:.2f} segundos")
            logging.info(f"Respuesta completa de Gemini: {respuesta}")

            # Guardar en historial
            self.save_historial(mensaje, respuesta)

            return respuesta
        except Exception as e:
            logging.error(f"Error al contactar Gemini: {str(e)}")
            return '{"intencion": "Conversar", "respuesta": "Lo siento, hubo un problema al conectarme."}'

    def charlar(self):
        print("¡Bienvenido al chat con DECSA! Escribe 'salir' para terminar.")
        while True:
            try:
                mensaje = input("Tú: ")
                if mensaje.lower() == "salir":
                    print("¡Hasta luego!")
                    break
                respuesta = self.generar_respuesta(mensaje)
                print(f"DECSA: {respuesta}")
            except KeyboardInterrupt:
                print("\n¡Hasta luego!")
                break
            except Exception as e:
                logging.error(f"Error en el bucle de chat: {str(e)}")
                print("Ocurrió un error. Intenta de nuevo.")


if __name__ == "__main__":
    try:
        test = GeminiTest()
        test.charlar()
    except Exception as e:
        logging.error(f"Error al iniciar el script: {str(e)}")
        print(f"No se pudo iniciar el chat: {str(e)}")