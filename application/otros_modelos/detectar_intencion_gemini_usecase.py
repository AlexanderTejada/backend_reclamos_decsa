#application/detectar_intencion_gemini_usecase.py
from application.otros_modelos.gemini_service import GeminiService

class DetectarIntencionGeminiUseCase:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    def ejecutar(self, mensaje):
        return self.gemini_service.detectar_intencion(mensaje)

    def ejecutar_con_historial(self, mensaje, historial):
        return self.gemini_service.detectar_intencion(mensaje, historial)