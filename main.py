from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO

from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.enum.text import WD_BREAK
from docx.shared import Pt

__VERSION__ = "2025-08-27-6"
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

def cleanup_after_header(header_par: Paragraph, doc: Document) -> Optional[Table]:
    """
    Après l'en-tête, supprime paragraphes vides et étiquettes individuelles
    (📌Rép., 📐Dim., 🧩Typo., 🎯, 🏷, 🔧, 🧾) jusqu'au premier tableau ou un contenu utile.
    Retourne le premier tableau trouvé si présent.
    """
    tokens = ["📌Rép.", "📐Dim.", "🧩Typo.", "🎯", "🏷", "🔧", "🧾"]
    items = list(block_items(doc))
    try:
        idx = next(i for i, it in enumerate(items) if isinstance(it, Paragraph) and it._p is header_par._p)
    except StopIteration:
        return None

    j = idx + 1
    first_table = None
    while j < len(items):
        it = items[j]
        if isinstance(it, Table):
            first_table = it
            break
        if isinstance(it, Paragraph):
            txt = it.text.strip()
            if txt == "" or any(txt.startswith(t) for t in tokens):
                remove_paragraph(it)
                items.pop(j)
                continue
            else:
                break
        j += 1
    return first_table

# ---------- Routes ----------
@app.get("/")
def root():
    return {"message": "Marchia Cloud Consultation en ligne", "version": __VERSION__}

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement", "data": req.model_dump()}

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
            p.text = p.text.replace("{{lot}}", req.lot)

    # 4) Descriptif au marqueur (accepte [[...]] ou {{...}})
    p_desc = find_paragraph(doc, ["[[DESCRIPTIF_CCTP]]", "{{DESCRIPTIF_CCTP}}"])
    if p_desc:
        p_desc.text = req.descriptif

    # 5) Tableau quantitatif : en-tête + nettoyage + tableau en haut de page 2
    p_tbl = find_paragraph(doc, ["[[TABLEAU_QUANTITATIF]]", "{{TABLEAU_QUANTITATIF}}"])
    if p_tbl and req.lignes:
        header_text = "📌Rép. 📐Dim. 🧩Typo. 🎯 (Rw+Ctr/Uw) 🏷Qté 🔧pose (applique/réno/tableau/feuillure) 🧾Commentaire"

        # 5a) Saut de page + transformation du marqueur en en-tête (une seule ligne)
        p_tbl.text = ""
        run = p_tbl.add_run()
        run.add_break(WD_BREAK.PAGE)
        run.add_text(header_text)
        header_par = p_tbl

        # 5b) Nettoyer ce qui suit immédiatement (étiquettes individuelles + vides)
        existing_table = cleanup_after_header(header_par, doc)

        headers = ["Rép.", "Dim.", "Typo.", "Perf. (Uw / Rw+Ctr)", "Qté", "Pose", "Commentaire"]

        if existing_table is None:
            # 5c) Créer un tableau neuf et l'insérer immédiatement après l'en-tête
            dest_table = doc.add_table(rows=1, cols=len(headers))
            hdr = dest_table.rows[0].cells
            for i, h in enumerate(headers):
                hdr[i].text = h
            header_par._p.addnext(dest_table._tbl)
        else:
            # 5d) Repositionner le tableau immédiatement après l'en-tête & purger les anciennes lignes
            dest_table = existing_table
            move_table_after_paragraph(dest_table, header_par)
            clear_table_body_keep_header(dest_table)
            hdr = dest_table.rows[0].cells
            for i, h in enumerate(headers[:len(hdr)]):
                hdr[i].text = h

        # 5e) Remplir les lignes
        for L in req.lignes:
            row = dest_table.add_row().cells
            row[0].text = L.rep
            row[1].text = L.dim
            row[2].text = L.typo
            row[3].text = L.perf
            row[4].text = str(int(L.qte))
            row[5].text = L.pose
            row[6].text = (L.commentaire or "").strip()

        # 5f) Style & espacement
        try:
            dest_table.style = "Table Grid"
        except Exception:
            pass
        zero_cell_spacing(dest_table)

    # 6) Export DOCX
    buf = BytesIO()
    doc.save(buf)
    content = buf.getvalue()

    filename = f'fiche_{req.projet.replace(" ", "_")}.docx'
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
