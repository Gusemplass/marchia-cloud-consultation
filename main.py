from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from io import BytesIO
from docx import Document

__VERSION__ = "2025-08-26-1"
app = FastAPI()

class FicheRequest(BaseModel):
    projet: str
    moa: str
    lot: str
    descriptif: str

@app.get("/")
def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !", "version": __VERSION__}

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    # Mode debug JSON si demandé explicitement
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement ✅", "data": req.model_dump()}

    # Génère un DOCX en mémoire
    doc = Document()
    doc.add_heading(f"Fiche consultation – {req.projet}", level=1)
    doc.add_paragraph(f"Maître d’ouvrage : {req.moa}")
    doc.add_paragraph(f"Lot : {req.lot}")
    doc.add_paragraph("Descriptif :")
    doc.add_paragraph(req.descriptif)

    tbl = doc.add_table(rows=1, cols=6)
    for i, h in enumerate(["Réf.", "Dim.", "Typo", "Perf.", "Qté", "Pose"]):
        tbl.rows[0].cells[i].text = h

    buf = BytesIO()
    doc.save(buf)
    content = buf.getvalue()

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="fiche_test.docx"'}
    )



