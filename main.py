from fastapi import FastAPI
from pydantic import BaseModel
from io import BytesIO
from docx import Document
from fastapi.responses import StreamingResponse

app = FastAPI()

class FicheRequest(BaseModel):
    projet: str
    moa: str
    lot: str
    descriptif: str

@app.get("/")
def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !"}

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest):
    # --- Génération DOCX en mémoire ---
    doc = Document()
    doc.add_heading(f"Fiche consultation – {req.projet}", level=1)
    doc.add_paragraph(f"Maître d’ouvrage : {req.moa}")
    doc.add_paragraph(f"Lot : {req.lot}")
    doc.add_paragraph("Descriptif :")
    doc.add_paragraph(req.descriptif)

    # Mini tableau type pour rassurer Word (structure non vide)
    table = doc.add_table(rows=1, cols=6)
    hdr = table.rows[0].cells
    hdr[0].text = "Réf."
    hdr[1].text = "Dim."
    hdr[2].text = "Typo"
    hdr[3].text = "Perf."
    hdr[4].text = "Qté"
    hdr[5].text = "Pose"

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    filename = f"fiche_{req.projet.replace(' ', '_')}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


