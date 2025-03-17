import requests

LLAMA_URL = "http://localhost:11434/api/generate"


def llama_request(prompt, history=[]):
    """
    Envia una consulta a Llama 3 y mantiene el historial de la conversación.
    """
    full_prompt = "\n".join(history) + f"\nUsuario: {prompt}\nAsistente:"

    payload = {
        "model": "llama3:latest",
        "prompt": full_prompt,
        "stream": False
    }

    try:
        response = requests.post(LLAMA_URL, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()["response"].strip()
        return "Error en LLM"
    except Exception as e:
        return f"Error conectando a Llama 3: {e}"


# Test de memoria
history = []
print("Test de memoria Llama 3. Escribe 'salir' para terminar.\n")

while True:
    user_input = input("Tú: ")
    if user_input.lower() == "salir":
        break

    response = llama_request(user_input, history)
    history.append(f"Usuario: {user_input}")
    history.append(f"Asistente: {response}")

    print(f"Llama 3: {response}")
