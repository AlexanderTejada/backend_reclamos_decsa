#aapplication/ detectar_intencion_usecase.py
from application.llama_service import LlamaService

class DetectarIntencionUseCase:
    def __init__(self, llama_service: LlamaService):
        self.llama_service = llama_service

    def ejecutar(self, mensaje):
        """Detecta la intención del mensaje usando Llama 3."""
        return self.llama_service.detectar_intencion(mensaje)
