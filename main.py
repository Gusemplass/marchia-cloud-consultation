from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from docx import Document
import tempfile
import os

app = FastAPI()

# ✅ Healthcheck
@app.get("/")
def read_root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !"}

# ✅ Modèle de données pour /genere-fiche
class FicheRequest(BaseModel):
    projet: str
    moa: str
    lot: str
    descriptif: str | None = None

# ✅ Endpoint /genere-fiche
@app.post("/genere-fiche")
async def genere_fiche(request: FicheRequest):
    # 1. Création d’un document Word
    doc = Document()

    # 2. Ajout des infos reçues
    doc.add_heading("📑 Fiche Consultation Fournisseur", level=1)
    doc.add_paragraph(f"🛠 Projet : {request.projet}")
    doc.add_paragraph(f"🏢 Maître d’ouvrage : {request.moa}")
    doc.add_paragraph(f"📦 Lot : {request.lot}")

    if request.descriptif:
        doc.add_paragraph(f"📎 Descriptif : {request.descriptif}")

    doc.add_paragraph("\n✅ Fiche générée automatiquement par Marchia Cloud")

    # 3. Sauvegarde temporaire
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "fiche_consultation.docx")
    doc.save(file_path)

    # 4. Retour du fichier
    return FileResponse(
        path=file_path,
        filename="fiche_consultation.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
