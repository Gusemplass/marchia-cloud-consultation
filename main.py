from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modèle pour recevoir les données
class FicheRequest(BaseModel):
    docstore: dict

@app.get("/")
async def root():
    return {"message": "✅ marchia-cloud-consultation is running !"}

@app.post("/genere-fiche")
async def genere_fiche(data: FicheRequest):
    docstore = data.docstore or {}

    # Vérifie la présence du mot "amiante"
    has_amiante = False
    if isinstance(docstore, dict):
        if ("amiante" in " ".join(docstore.get("files", [])).lower()
                or "amiante" in " ".join(docstore.get("text", [])).lower()):
            has_amiante = True

    # 👉 Ici tu mets ton traitement habituel (ajout annexe, génération fiche, etc.)
    # Pour test, je renvoie juste un message
    return {
        "status": "ok",
        "has_amiante": has_amiante,
        "files": docstore.get("files", []),
    }
