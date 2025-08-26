from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO

from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.enum.text import WD_BREAK
from docx.shared import Pt

__VERSION__ = "2025-08-26-5"
TEMPLATE_PATH = "templates/fiche_demo_MARCHIA_full.docx"

app = FastAPI()

# ---------- Modèles ----------
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

# ---------- Helpers ----------
def find_paragraph(doc: Document, needles: List[str]) -> Optional[Paragraph]:
    for p in doc.paragraphs:
        for n in needles:
            if n in p.text:
                return p
    return None

def block_items(doc: Document):
    """Yield Paragraph/Table dans l'ordre d'apparition (de haut en bas)."""
    body = doc._element.body
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)

def remove_paragraph(p: Paragraph):
    p._element.getparent().remove(p._element)

def move_table_after_paragraph(table: Table, paragraph: Paragraph):
    tbl = table._tbl
    parent = tbl.getparent()
    parent.remove(tbl)
    paragraph._p.addnext(tbl)

def clear_table_body_keep_header(table: Table):
    """Supprime toutes les lignes sauf la première (entête)."""
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[1]._tr)

def zero_cell_spacing(table: Table):
    """Espace avant/après = 0 dans toutes les cellules (évite les blancs parasites)."""
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(0)
                pf.space_after = Pt(0)

# ---------- Routes ----------
@app.get("/")
def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !", "version": __VERSION__}

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement ✅", "data": req.model_dump()}

    # 1) Charger le modèle
    doc = Document(TEMPLATE_PATH)

    # 2) Calibri 11 global (style Normal)
    try:
        normal = doc.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)
    except Exception:
        pass

    # 3) Placeholder simples éventuels
    for p in doc.paragraphs:
        if "{{projet}}" in p.text:
            p.text = p.text.replace("{{projet}}", req.projet)
        if "{{moa}}" in p.text:
            p.text = p.text.replace("{{moa}}", req.moa)
        if "{{lot}}" in p.text:
            p.text = p.text.replace(





