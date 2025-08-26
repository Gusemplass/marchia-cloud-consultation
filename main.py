from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

# Root = healthcheck
@app.get("/")
def read_root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !"}

# Modèle attendu pour l’endpoint
class FicheRequest(BaseModel):
    projet: str
    moa: str
    lot: str
    descriptif: str | None = None

# Endpoint fictif pour tester la chaîne
@app.post("/genere-fiche")
async def genere_fiche(request: FicheRequest):
    # Pour l’instant on se contente de renvoyer ce qu’on a reçu
    return {
        "status": "ok",
        "message": "Fiche reçue correctement ✅",
        "data": request.dict()
    }
