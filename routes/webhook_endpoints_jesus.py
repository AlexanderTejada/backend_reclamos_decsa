from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI()

# Simula tu función de autenticación
def autentificar(token: str) -> bool:
    return token == "mi_token_secreto"

# Simula tu procesamiento
def ejecucionProcesar(data: dict):
    print("Procesando mensaje:", data)  # Aquí iría tu lógica

@app.api_route("/webhook/", methods=["GET", "POST"])
async def webhook_whatsapp(request: Request):
    if request.method == "GET":
        try:
            params = dict(request.query_params)
            token = params.get('hub.verify_token')
            challenge = params.get('hub.challenge')

            if autentificar(token):
                return PlainTextResponse(challenge)
            else:
                raise HTTPException(status_code=403, detail="Error de autenticación.")
        except Exception:
            raise HTTPException(status_code=500, detail="Error del servidor.")

    elif request.method == "POST":
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="No se recibió un JSON válido.")

        try:
            ejecucionProcesar(data)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Faltan datos necesarios ({e}).")

        return JSONResponse(content={"mensaje": "Datos recibidos y procesados correctamente."})
