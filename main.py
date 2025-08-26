from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
from docx import Document

__VERSION__ = "2025-08-26-2"  # <— V2
TEMPLATE_PATH = "templates/fiche_demo_MARCHIA_full.docx"

app = FastAPI()

# ---------- Schémas ----------
class LigneQuantitative(BaseModel):
    rep: str
    dim: str
    typo: str
    perf: str
    qte: int
    pose: str
    commentaire: Optional[str] = ""

class FicheRequest(BaseModel):
    projet: str
    moa: str
    lot: str
    descriptif: str
    lignes: Optional[List[LigneQuantitative]] = None

# ---------- Utils ----------
def find_paragraph(doc: Document, needle: str):
    for p in doc.paragraphs:
        if needle in p.text:
            return p
    return None

@app.get("/")
def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !", "version": __VERSION__}

# ---------- Route principale ----------
@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement ✅", "data": req.model_dump()}

    # 1) Charger le modèle
    doc = Document(TEMPLATE_PATH)

    # 2) Placeholder simples éventuels
    for p in doc.paragraphs:
        if "{{projet}}" in p.text: p.text = p.text.replace("{{projet}}", req.projet)
        if "{{moa}}" in p.text:    p.text = p.text.replace("{{moa}}", req.moa)
        if "{{lot}}" in p.text:    p.text = p.text.replace("{{lot}}", req.lot)

    # 3) Descriptif CCTP
    p_desc = find_paragraph(doc, "[[DESCRIPTIF_CCTP]]")
    if p_desc:
        p_desc.text = req.descriptif

    # 4) Tableau quanti
    p_tbl = find_paragraph(doc, "[[TABLEAU_QUANTITATIF]]")
    if p_tbl and req.lignes:
        table = doc.add_table(rows=1, cols=7)
        hdr = table.rows[0].cells
        hdr[0].text = "📌Rép."
        hdr[1].text = "📐Dim."
        hdr[2].text = "🧩Typo."
        hdr[3].text = "🎯Perf."
        hdr[4].text = "🏷Qté"
        hdr[5].text = "🔧Pose"
        hdr[6].text = "🧾Commentaire"

        for L in req.lignes:
            row = table.add_row().cells
            row[0].text = L.rep
            row[1].text = L.dim
            row[2].text = L.typo
            row[3].text = L.perf
            row[4].text = str(L.qte)
            row[5].text = L.pose
            row[6].text = (L.commentaire or "").strip()

        # (optionnel) un style de tableau Word si tu en as un : "Table Grid", etc.
        try:
            table.style = "Table Grid"
        except Exception:
            pass

        # Remplacer le marqueur et insérer le tableau juste après
        p_tbl.text = p_tbl.text.replace("[[TABLEAU_QUANTITATIF]]", "").strip()
        p_tbl._p.addnext(table._tbl)

    # 5) Retour DOCX
    buf = BytesIO(); doc.save(buf); content = buf.getvalue()
    filename = f'fiche_{req.projet.replace(" ", "_")}.docx'
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )




