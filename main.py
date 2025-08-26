from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !"}

@app.post("/genere-fiche")
async def genere_fiche(payload: dict):
    # simulation simple pour tester
    return {"status": "ok", "payload_recu": payload}
