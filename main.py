from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from docx import Document
import uuid
import os

app = FastAPI()

class FicheRequest(BaseModel):
    nom_chantier: str
    type_travaux: str
    produit: str
    descriptif: str

@app.post("/genere-fiche")
def genere_fiche(data: FicheRequest):
    template_path = "fiche_template.docx"
    doc = Document(template_path)

    # Remplacements simples dans les paragraphes
    for p in doc.paragraphs:
        if "NOM DE CHANTIER" in p.text:
            p.text = p.text.replace("NOM DE CHANTIER", data.nom_chantier)
        if "réhabilitation / neuf" in p.text:
            p.text = p.text.replace("réhabilitation / neuf", data.type_travaux)
        if "produit suivant" in p.text:
            p.text = p.text.replace("produit suivant", data.produit)
        if "📎 Descriptif issu du CCTP ou DPGF à compléter ci-après :" in p.text:
            p.add_run("\n" + data.descriptif)

    filename = f"fiche_{uuid.uuid4().hex[:8]}.docx"
    output_path = f"/tmp/{filename}"
    doc.save(output_path)

    return FileResponse(path=output_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
