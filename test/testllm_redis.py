import redis
import requests
import time

# Configuración de Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SESSION_TIMEOUT = 1800  # 30 minutos

# Conectar a Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Configuración de Llama 3
LLAMA_URL = "http://localhost:11434/api/generate"

def llama_request(prompt, user_id):
    """
    Envía un mensaje a Llama 3 con el historial del usuario almacenado en Redis.
    """
    # Recuperar historial desde Redis
    history = redis_client.lrange(f"user:{user_id}:history", 0, -1)
    full_prompt = "\n".join(history) + f"\nUsuario: {prompt}\nAsistente:"

    payload = {
        "model": "llama3:latest",
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(LLAMA_URL, json=payload, timeout=10)
        if response.status_code == 200:
            reply = response.json()["response"].strip()
        else:
            reply = "Error en LLM"
    except Exception as e:
        reply = f"Error conectando a Llama 3: {e}"

    # Guardar historial en Redis (máximo 10 mensajes)
    redis_client.rpush(f"user:{user_id}:history", f"Usuario: {prompt}")
    redis_client.rpush(f"user:{user_id}:history", f"Asistente: {reply}")
    redis_client.ltrim(f"user:{user_id}:history", -10, -1)  # Mantiene solo los últimos 10 mensajes
    redis_client.expire(f"user:{user_id}:history", SESSION_TIMEOUT)  # Expira en 30 min

    return reply

# Simulación de varios usuarios
print("Test de memoria con Redis y Llama 3. Escribe 'salir' para terminar.\n")

while True:
    user_id = input("Ingresa ID de usuario: ")  # Simula un usuario diferente
    user_input = input("Tú: ")
    if user_input.lower() == "salir":
        break

    response = llama_request(user_input, user_id)
    print(f"Llama 3: {response}")

    # Simulación de tiempo de espera (para probar la expiración)
    time.sleep(2)  # Simula que el usuario tarda en responder
