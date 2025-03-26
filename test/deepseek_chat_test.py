import logging
import time
from openai import OpenAI
from infrastructure.settings import Config  # Asegúrate de que esto esté configurado con tu API key

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DeepSeekTest:
    def __init__(self):
        self.client = OpenAI(api_key=Config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        logging.info("DeepSeekTest inicializado con API Key y endpoint configurados.")

    def generar_respuesta(self, mensaje):
        try:
            # Generar respuesta sin prompt estructurado
            logging.info(f"Mensaje enviado a DeepSeek: {mensaje}")
            start_time = time.time()
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Eres DECSA, un asistente virtual. Responde en texto simple (sin JSON)."},
                    {"role": "user", "content": mensaje},  # Mensaje directo, sin prompt adicional
                ],
                temperature=0.1,  # Bajo para respuestas rápidas
                max_tokens=50,   # Limitado para respuestas cortas
                stream=False     # Sin streaming, respuesta completa
            )
            http_ok_time = time.time()
            logging.info(f"Tiempo hasta HTTP 200 OK: {http_ok_time - start_time:.2f} segundos")

            # Obtener respuesta completa
            respuesta = response.choices[0].message.content.strip()
            total_time = time.time() - start_time
            logging.info(f"Tiempo total de generación: {total_time:.2f} segundos")
            logging.info(f"Respuesta completa de DeepSeek: {respuesta}")

            return respuesta
        except Exception as e:
            logging.error(f"Error al contactar DeepSeek: {str(e)}")
            return "Lo siento, hubo un problema al conectarme."

    def charlar(self):
        print("¡Bienvenido al chat con DECSA! Escribe 'salir' para terminar.")
        while True:
            mensaje = input("Tú: ")
            if mensaje.lower() == "salir":
                print("¡Hasta luego!")
                break
            respuesta = self.generar_respuesta(mensaje)
            print(f"DECSA: {respuesta}")

if __name__ == "__main__":
    test = DeepSeekTest()
    test.charlar()