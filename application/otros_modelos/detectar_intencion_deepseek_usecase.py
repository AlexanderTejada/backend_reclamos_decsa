from application.otros_modelos.deepseek_service import DeepSeekService

class DetectarIntencionDeepSeekUseCase:
    def __init__(self, deepseek_service: DeepSeekService):
        self.deepseek_service = deepseek_service

    def ejecutar(self, mensaje):
        return self.deepseek_service.detectar_intencion(mensaje)

    def ejecutar_con_historial(self, mensaje, historial):
        return self.deepseek_service.detectar_intencion(mensaje, historial)
