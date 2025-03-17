import streamlit as st
import requests

st.title("Chatbot DECSA - LLaMA con Respuestas Naturales")

# Inicializar variables de sesión
if "dni" not in st.session_state:
    st.session_state["dni"] = None
if "nombre_usuario" not in st.session_state:
    st.session_state["nombre_usuario"] = None
if "flujo" not in st.session_state:
    st.session_state["flujo"] = None
if "esperando_dni" not in st.session_state:
    st.session_state["esperando_dni"] = False
if "confirmado" not in st.session_state:
    st.session_state["confirmado"] = False
if "esperando_accion" not in st.session_state:
    st.session_state["esperando_accion"] = False
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "historial" not in st.session_state:
    st.session_state["historial"] = []

# Mostrar mensajes previos
for msg in st.session_state["messages"]:
    st.write(msg)

# Input del usuario
user_input = st.text_input("Escribe tu mensaje:")
if st.button("Enviar") and user_input:
    # Agregar el mensaje del usuario al historial
    st.session_state["messages"].append(f"👤 Tú: {user_input}")
    st.session_state["historial"].append(f"Usuario: {user_input}")

    # Preparar el historial reciente para LLaMA
    historial_reciente = "\n".join(st.session_state["historial"][-6:]) if st.session_state["historial"] else "No hay historial previo."

    # Fase 1: Usar LLaMA para detectar la intención inicial con respuestas naturales y variadas
    if not st.session_state["flujo"] and not st.session_state["esperando_dni"] and not st.session_state["confirmado"]:
        prompt = f"""
        Eres el asistente virtual de DECSA, diseñado para conversar de manera profesional, natural y amigable. 
        Tu tarea es interpretar el mensaje del usuario, clasificar su intención y responder de forma variada, evitando repetir siempre lo mismo. 
        Aquí tienes el historial reciente:

        Historial reciente (últimos 6 mensajes):
        {historial_reciente}

        Mensaje actual del usuario: "{user_input}"

        Instrucciones:
        1. Clasifica la intención del usuario en una de las siguientes categorías:
           - Realizar un reclamo
           - Actualizar datos
           - Consultar el estado de su reclamo
           - Conversar (si solo quiere hablar sin una intención específica)
        2. Genera una respuesta conversacional profesional, natural y única basada en la intención:
           - Si es "Conversar", sigue la conversación amigablemente y sugiere opciones de forma sutil (ej. realizar un reclamo, actualizar datos o consultar un reclamo).
           - Si es una acción específica, confirma la intención de manera natural y pide el DNI sin que suene repetitivo.
           - Siempre incluye, de forma fluida, lo que el usuario puede hacer (realizar un reclamo, actualizar datos o consultar un reclamo).
           - Varía el tono y las palabras para que las respuestas no sean idénticas cada vez.

        Devuelve la intención y la respuesta en este formato:
        Intención: [categoría]
        Respuesta: [tu respuesta aquí]

        Ejemplos de variedad para "Hola":
        - Intención: Conversar, Respuesta: ¡Hola! Me alegra verte por aquí. ¿Qué te trae hoy? Puedo ayudarte con un reclamo, actualizar tus datos o revisar el estado de algo si quieres.
        - Intención: Conversar, Respuesta: Hola, ¿qué tal? Estoy listo para charlar o ayudarte con lo que necesites, como hacer un reclamo o cambiar algún dato.
        - Intención: Conversar, Respuesta: ¡Hola! ¿En qué andas pensando? Si quieres, podemos hablar o trabajar en algo como un reclamo o una consulta.

        Ejemplos para intenciones específicas:
        - Mensaje: "quiero acer un reclemo" -> Intención: Realizar un reclamo, Respuesta: Veo que quieres hacer un reclamo, ¿me pasas tu DNI para que empecemos con eso? También puedo ayudarte con datos o consultas si cambias de idea.
        - Mensaje: "necesito cambiar mi correo" -> Intención: Actualizar datos, Respuesta: Claro, podemos actualizar tu correo. ¿Me das tu DNI para proceder? Por si acaso, también puedo ayudarte con reclamos o consultas.
        - Mensaje: "solo quiero hablar" -> Intención: Conversar, Respuesta: ¡Genial! Me gusta charlar. ¿Qué tienes en mente? Si en algún momento quieres hacer un reclamo o actualizar algo, solo dime.
        """
        payload = {"model": "llama3:latest", "prompt": prompt, "stream": False}
        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=10)
            if response.status_code == 200:
                response_text = response.json()["response"].strip()
                intencion_line = response_text.split("\n")[0]
                respuesta_line = "\n".join(response_text.split("\n")[1:])
                intencion = intencion_line.replace("Intención: ", "").strip("[]")
                respuesta = respuesta_line.replace("Respuesta: ", "").strip()
            else:
                intencion = "Conversar"
                respuesta = "Hola, ¿qué tal? No entendí bien, pero estoy aquí para charlar o ayudarte con un reclamo, datos o consultas."
        except Exception as e:
            intencion = "Conversar"
            respuesta = "Ups, algo falló. ¿Qué tal si charlamos o vemos qué puedes hacer, como un reclamo o actualizar algo?"

        st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
        st.session_state["historial"].append(f"Bot: {respuesta}")

        # Si LLaMA detecta una intención específica, activar el flujo estructurado
        if intencion in ["Realizar un reclamo", "Actualizar datos", "Consultar el estado de su reclamo"]:
            st.session_state["flujo"] = intencion
            st.session_state["esperando_dni"] = True

    # Fase 2: Esperar y validar el DNI
    elif st.session_state["esperando_dni"]:
        dni_info = None
        try:
            response = requests.get(f"http://127.0.0.1:5000/api/usuarios/{user_input}")
            if response.status_code == 200:
                user_data = response.json()
                dni_info = (user_data["DNI"], user_data["NOMBRE"], user_data["APELLIDO"])
        except:
            dni_info = None

        if dni_info:
            st.session_state["dni"] = user_input
            st.session_state["nombre_usuario"] = f"{dni_info[1]} {dni_info[2]}"
            respuesta = f"¿Eres {dni_info[1]} {dni_info[2]}? (Responde 'sí' o 'no')"
            st.session_state["esperando_dni"] = False
        else:
            respuesta = "No encontré ese DNI en el sistema. Por favor, verifica el número e intenta de nuevo."

        st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
        st.session_state["historial"].append(f"Bot: {respuesta}")

    # Fase 3: Confirmar identidad y avanzar
    elif not st.session_state["esperando_dni"] and not st.session_state["confirmado"]:
        if user_input.lower() in ["sí", "si"]:
            st.session_state["confirmado"] = True
            if st.session_state["flujo"] == "Consultar el estado de su reclamo":
                dni = st.session_state["dni"]
                try:
                    response = requests.get(f"http://127.0.0.1:5000/api/reclamos/{dni}")
                    if response.status_code == 200:
                        reclamos = response.json()
                        if reclamos:
                            respuesta = "Aquí están tus reclamos:\n" + "\n".join(
                                [f"ID: {r['ID_RECLAMO']} - Estado: {r['ESTADO']}" for r in reclamos])
                        else:
                            respuesta = "No tienes reclamos registrados."
                    else:
                        respuesta = "No tienes reclamos registrados."
                except:
                    respuesta = "Hubo un error al consultar el estado de tus reclamos."

                st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
                st.session_state["historial"].append(f"Bot: {respuesta}")

                # Generar resumen y resetear
                prompt_resumen = f"""
                Un usuario ha interactuado con el bot de DECSA y ha completado una acción. 
                Este es su historial de interacción (últimos 6 mensajes):
                {chr(10).join(st.session_state['historial'][-6:])}
                Resume lo que hizo el usuario en una frase profesional.
                """
                payload_resumen = {"model": "llama3:latest", "prompt": prompt_resumen, "stream": False}
                try:
                    response_resumen = requests.post("http://localhost:11434/api/generate", json=payload_resumen, timeout=10)
                    resumen = response_resumen.json()["response"].strip() if response_resumen.status_code == 200 else "No pude generar un resumen."
                    st.session_state["messages"].append(f"🤖 Bot: Resumen: {resumen}")
                    st.session_state["historial"].append(f"Bot: Resumen: {resumen}")
                except:
                    st.session_state["messages"].append(f"🤖 Bot: No pude generar un resumen.")

                # Resetear el estado
                st.session_state["flujo"] = None
                st.session_state["dni"] = None
                st.session_state["nombre_usuario"] = None
                st.session_state["confirmado"] = False
                st.session_state["esperando_dni"] = False
                st.session_state["esperando_accion"] = False
            else:
                st.session_state["esperando_accion"] = True
                respuesta = f"Gracias, {st.session_state['nombre_usuario']}. Procedamos con {st.session_state['flujo']}. ¿Qué necesitas?"
                st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
                st.session_state["historial"].append(f"Bot: {respuesta}")
        elif user_input.lower() == "no":
            st.session_state["dni"] = None
            st.session_state["esperando_dni"] = True
            respuesta = "Entendido. Por favor, ingresa otro DNI."
            st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
            st.session_state["historial"].append(f"Bot: {respuesta}")
        else:
            respuesta = "Por favor, responde 'sí' o 'no' para confirmar tu identidad."
            st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
            st.session_state["historial"].append(f"Bot: {respuesta}")

    # Fase 4: Ejecutar la acción específica
    elif st.session_state["confirmado"] and st.session_state["esperando_accion"]:
        if st.session_state["flujo"] == "Realizar un reclamo":
            try:
                response = requests.post(f"http://127.0.0.1:5000/api/reclamos/",
                                        json={"dni": st.session_state["dni"], "descripcion": user_input})
                if response.status_code == 201:
                    respuesta = "Tu reclamo ha sido registrado con éxito."
                else:
                    respuesta = "Hubo un error al registrar tu reclamo."
            except:
                respuesta = "Hubo un error al registrar tu reclamo."

            st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
            st.session_state["historial"].append(f"Bot: {respuesta}")

            # Generar resumen y resetear
            prompt_resumen = f"""
            Un usuario ha interactuado con el bot de DECSA y ha completado una acción. 
            Este es su historial de interacción (últimos 6 mensajes):
            {chr(10).join(st.session_state['historial'][-6:])}
            Resume lo que hizo el usuario en una frase profesional.
            """
            payload_resumen = {"model": "llama3:latest", "prompt": prompt_resumen, "stream": False}
            try:
                response_resumen = requests.post("http://localhost:11434/api/generate", json=payload_resumen, timeout=10)
                resumen = response_resumen.json()["response"].strip() if response_resumen.status_code == 200 else "No pude generar un resumen."
                st.session_state["messages"].append(f"🤖 Bot: Resumen: {resumen}")
                st.session_state["historial"].append(f"Bot: Resumen: {resumen}")
            except:
                st.session_state["messages"].append(f"🤖 Bot: No pude generar un resumen.")

            # Resetear el estado
            st.session_state["flujo"] = None
            st.session_state["dni"] = None
            st.session_state["nombre_usuario"] = None
            st.session_state["confirmado"] = False
            st.session_state["esperando_dni"] = False
            st.session_state["esperando_accion"] = False

        elif st.session_state["flujo"] == "Actualizar datos":
            if "correo" in user_input.lower() or "celular" in user_input.lower():
                campo = "MAIL" if "correo" in user_input.lower() else "CELULAR"
                respuesta = f"Por favor, dime el nuevo {campo.lower()} que quieres registrar."
                st.session_state["flujo"] = f"Actualizar {campo}"
            else:
                respuesta = "Por favor, dime si quieres actualizar tu correo o tu celular."
            st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
            st.session_state["historial"].append(f"Bot: {respuesta}")

    # Fase 5: Actualizar datos específicos
    elif st.session_state["flujo"].startswith("Actualizar "):
        campo = st.session_state["flujo"].split(" ")[1]
        try:
            response = requests.put(f"http://127.0.0.1:5000/api/usuarios/{st.session_state['dni']}",
                                    json={campo: user_input})
            if response.status_code == 200:
                respuesta = "Tus datos han sido actualizados correctamente."
            else:
                respuesta = "Hubo un error al actualizar tus datos."
        except:
            respuesta = "Hubo un error al actualizar tus datos."

        st.session_state["messages"].append(f"🤖 Bot: {respuesta}")
        st.session_state["historial"].append(f"Bot: {respuesta}")

        # Generar resumen y resetear
        prompt_resumen = f"""
        Un usuario ha interactuado con el bot de DECSA y ha completado una acción. 
        Este es su historial de interacción (últimos 6 mensajes):
        {chr(10).join(st.session_state['historial'][-6:])}
        Resume lo que hizo el usuario en una frase profesional.
        """
        payload_resumen = {"model": "llama3:latest", "prompt": prompt_resumen, "stream": False}
        try:
            response_resumen = requests.post("http://localhost:11434/api/generate", json=payload_resumen, timeout=10)
            resumen = response_resumen.json()["response"].strip() if response_resumen.status_code == 200 else "No pude generar un resumen."
            st.session_state["messages"].append(f"🤖 Bot: Resumen: {resumen}")
            st.session_state["historial"].append(f"Bot: Resumen: {resumen}")
        except:
            st.session_state["messages"].append(f"🤖 Bot: No pude generar un resumen.")

        # Resetear el estado
        st.session_state["flujo"] = None
        st.session_state["dni"] = None
        st.session_state["nombre_usuario"] = None
        st.session_state["confirmado"] = False
        st.session_state["esperando_dni"] = False
        st.session_state["esperando_accion"] = False

    st.rerun()