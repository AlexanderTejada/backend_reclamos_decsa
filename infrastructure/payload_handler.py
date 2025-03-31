# infrastructure/payload_handler.py
import os
import logging
from fastapi import Request
from typing import Dict, Optional
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Log para verificar el token
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "tu_token_de_acceso_1")
logging.info(f"WHATSAPP_TOKEN leído: {WHATSAPP_TOKEN[:10]}...")  # Mostrar solo los primeros 10 caracteres por seguridad

CLIENTS_CONFIG = {
    "498540436679293": {
        "token": WHATSAPP_TOKEN,
        "display_phone_number": "+1 555 165 3595"
    },
}

ALLOWED_DESTINATIONS = [
    "5492646026190",
    "5492645513572"
]

class PayloadHandler:
    @staticmethod
    async def parse_chattigo_payload(request: Request) -> Dict[str, Dict[str, str]]:
        """Parsea el payload de Chattigo al formato esperado por ChattigoAdapter."""
        data = await request.json()
        user_id = data.get("user_id")
        text = data.get("message", {}).get("text", "")
        if not user_id or not text:
            raise ValueError("Payload de Chattigo inválido")
        return {"user_id": user_id, "message": {"text": text}}

    @staticmethod
    async def parse_whatsapp_payload(request: Request) -> Optional[Dict]:
        """Parsea el payload de WhatsApp y extrae información adicional."""
        data = await request.json()
        try:
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})

            # Verificar si el payload contiene mensajes o estados
            if "messages" in value:
                message = value.get("messages", [])[0]
                user_id = message.get("from")  # Número del usuario (wa_id)
                text = message.get("text", {}).get("body", "")
                phone_number_id = value.get("metadata", {}).get("phone_number_id")  # ID del número de teléfono
                display_phone_number = value.get("metadata", {}).get("display_phone_number")  # Número de teléfono
                profile_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "Usuario")

                if not user_id or not text:
                    raise ValueError("Payload de WhatsApp inválido")

                # Validar que el número de destino esté permitido (en modo de prueba)
                if user_id not in ALLOWED_DESTINATIONS:
                    logging.warning(f"Número de destino no permitido: {user_id}")
                    raise ValueError(f"No se puede enviar mensajes al número {user_id}. Debe estar en la lista de números permitidos.")

                logging.info(f"Payload parseado: user_id={user_id}, text={text}, phone_number_id={phone_number_id}")
                return {
                    "user_id": user_id,
                    "message": {"text": text},
                    "phone_number_id": phone_number_id,
                    "display_phone_number": display_phone_number,
                    "profile_name": profile_name
                }
            elif "statuses" in value:
                # Manejar notificaciones de estado (sent, delivered, read, etc.)
                status = value.get("statuses", [])[0]
                status_type = status.get("status")
                recipient_id = status.get("recipient_id")
                logging.info(f"Recibida notificación de estado: {status_type} para el mensaje enviado a {recipient_id}")
                # Devolver None para indicar que no se requiere procesamiento adicional
                return None
            else:
                raise ValueError("Payload de WhatsApp inválido: no contiene mensajes ni estados")

        except Exception as e:
            logging.error(f"Error al parsear payload de WhatsApp: {str(e)}")
            raise ValueError("Formato de payload de WhatsApp inválido")

    @staticmethod
    async def send_response(platform: str, user_id: str, text: str, extra_data: Dict = None) -> Dict:
        """Envía la respuesta según la plataforma."""
        extra_data = extra_data or {}
        if platform == "chattigo":
            # Chattigo espera que devuelvas la respuesta en el webhook
            return {"response": text, "user_id": user_id}
        elif platform == "whatsapp":
            # WhatsApp requiere una solicitud HTTP para enviar la respuesta
            phone_number_id = extra_data.get("phone_number_id")
            if not phone_number_id:
                raise RuntimeError("No se proporcionó WHATSAPP_PHONE_ID en el payload")

            # Buscar el token correspondiente al phone_number_id
            client_config = CLIENTS_CONFIG.get(phone_number_id)
            if not client_config:
                raise RuntimeError(f"No se encontró configuración para WHATSAPP_PHONE_ID: {phone_number_id}")

            token = client_config["token"]
            if not token:
                raise RuntimeError(f"No se encontró WHATSAPP_TOKEN para WHATSAPP_PHONE_ID: {phone_number_id}")

            # Normalizar el número de destino para números argentinos
            normalized_user_id = user_id
            if user_id.startswith("549"):  # Formato argentino con +549
                normalized_user_id = "54" + user_id[3:]  # Convertir a +54 sin el 9 adicional
                logging.info(f"Normalizado user_id de {user_id} a {normalized_user_id}")

            url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": normalized_user_id,
                "type": "text",
                "text": {"body": text}
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    logging.info(f"Mensaje enviado a {normalized_user_id}: {text}")
                else:
                    logging.error(f"Error al enviar mensaje a WhatsApp: {response.text}")
                return {"status": response.status_code}
        else:
            raise ValueError(f"Plataforma no soportada: {platform}")