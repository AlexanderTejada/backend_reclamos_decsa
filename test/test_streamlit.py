import streamlit as st
import redis
import requests

# Configuración de Redis y Llama 3
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SESSION_TIMEOUT = 1800  # 30 minutos
LLAMA_URL = "http://localhost:11434/api/generate"

# Conectar a Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def llama_request(prompt, user_id):
    """
    Envia un mensaje a Llama 3 con el historial del usuario almacenado en Redis.
    """
    history = redis_client.lrange(f"user:{user_id}:history", 0, -1)
    full_prompt = "\n".join(history) + f"\nUsuario: {prompt}\nAsistente:"

    payload = {"model": "llama3:latest", "prompt": full_prompt, "stream": False}

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
    redis_client.ltrim(f"user:{user_id}:history", -10, -1)
    redis_client.expire(f"user:{user_id}:history", SESSION_TIMEOUT)

    return reply

# Interfaz en Streamlit
st.title("Chatbot de Reclamos (Prueba en Streamlit)")

# Simulación de usuario (cada vez que alguien entra a la página, se genera un user_id único)
user_id = st.session_state.get("user_id", "test_user")
st.session_state["user_id"] = user_id

# Área de conversación
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Mostrar mensajes previos
for msg in st.session_state["messages"]:
    st.write(msg)

# Input del usuario
user_input = st.text_input("Escribe tu mensaje:")

if st.button("Enviar") and user_input:
    response = llama_request(user_input, user_id)
    st.session_state["messages"].append(f"👤 Tú: {user_input}")
    st.session_state["messages"].append(f"🤖 Bot: {response}")

    # Refrescar la página para mostrar los mensajes actualizados
    st.rerun()
