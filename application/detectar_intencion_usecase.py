from application.llama_service import LlamaService

class DetectarIntencionUseCase:
    def __init__(self, llama_service: LlamaService):
        self.llama_service = llama_service

    def ejecutar(self, mensaje):
        """Detecta la intención del mensaje usando Llama 3 sin historial (compatibilidad con el código original)."""
        return self.llama_service.detectar_intencion(mensaje)

    def ejecutar_con_historial(self, mensaje, historial):
        """Detecta la intención del mensaje usando Llama 3 con historial de conversación."""
        return self.llama_service.detectar_intencion(mensaje, historial)