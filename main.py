from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
from docx import Document

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

# Endpoint pour générer une fiche Word
@app.post("/genere-fiche")
async def genere_fiche(request: FicheRequest):
    # Création du document Word
    doc = Document()
    doc.add_heading(f"Fiche Consultation - {request.projet}", level=1)
    doc.add_paragraph(f"Maître d’ouvrage : {request.moa}")
    doc.add_paragraph(f"Lot concerné : {request.lot}")
    if request.descriptif:
        doc.add_paragraph(f"Descriptif : {request.descriptif}")

    # Sauvegarde temporaire
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)

    # Envoi du fichier Word
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"fiche_{request.projet.replace(' ', '_')}.docx"
    )

