# application/detectar_intencion_chatgpt_usecase.py
from application.chatgpt_service import ChatGPTService

class DetectarIntencionChatGPTUseCase:
    def __init__(self, chatgpt_service: ChatGPTService):
        self.chatgpt_service = chatgpt_service

    def ejecutar(self, mensaje):
        return self.chatgpt_service.detectar_intencion(mensaje)

    def ejecutar_con_historial(self, mensaje, historial):
        return self.chatgpt_service.detectar_intencion(mensaje, historial)