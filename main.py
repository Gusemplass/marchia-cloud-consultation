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
            p.text = p.text.replace("{{lot}}", req.lot)

    # 4) Descriptif au marqueur (accepte [[...]] ou {{...}})
    p_desc = find_paragraph(doc, ["[[DESCRIPTIF_CCTP]]", "{{DESCRIPTIF_CCTP}}"])
    if p_desc:
        p_desc.text = req.descriptif

    # 5) Tableau quantitatif au marqueur
    p_tbl = find_paragraph(doc, ["[[TABLEAU_QUANTITATIF]]", "{{TABLEAU_QUANTITATIF}}"])
    if p_tbl and req.lignes:
        # 5a) Effacer le marqueur et forcer un saut de page (début page suivante)
        p_tbl.text = ""
        run = p_tbl.add_run()
        run.add_break(WD_BREAK.PAGE)

        # 5b) Chercher le premier tableau APRÈS ce paragraphe
        items = list(block_items(doc))
        try:
            start_idx = next(i for i, it in enumerate(items) if isinstance(it, Paragraph) and it._p is p_tbl._p)
        except StopIteration:
            start_idx = None

        dest_table: Optional[Table] = None
        end_idx = None
        if start_idx is not None:
            for j in range(start_idx + 1, len(items)):
                if isinstance(items[j], Table):
                    dest_table = items[j]
                    end_idx = j
                    break

        if dest_table is None:
            # 5c) Pas de tableau existant → en créer un "propre" avec entête et l'insérer juste après le marqueur
            dest_table = doc.add_table(rows=1, cols=7)
            hdr = dest_table.rows[0].cells
            hdr[0].text = "Rép."
            hdr[1].text = "Dim."
            hdr[2].text = "Typo."
            hdr[3].text = "Perf. (Uw / Rw+Ctr)"
            hdr[4].text = "Qté"
            hdr[5].text = "Pose"
            hdr[6].text = "Commentaire"
            p_tbl._p.addnext(dest_table._tbl)
        else:
            # 5d) Supprimer tous les paragraphes entre le marqueur et le tableau
            for it in items[start_idx + 1:end_idx]:
                if isinstance(it, Paragraph):
                    remove_paragraph(it)
            # 5e) Déplacer le tableau juste après le marqueur (haut de page 2)
            move_table_after_paragraph(dest_table, p_tbl)
            # 5f) Nettoyer le corps et uniformiser l'entête
            clear_table_body_keep_header(dest_table)
            hdr = dest_table.rows[0].cells
            headers = ["Rép.", "Dim.", "Typo.", "Perf. (Uw / Rw+Ctr)", "Qté", "Pose", "Commentaire"]
            for i, h in enumerate(headers[:len(hdr)]):
                hdr[i].text = h

        # 5g) Remplir les lignes
        for L in req.lignes:
            row = dest_table.add_row().cells
            row[0].text = L.rep
            row[1].text = L.dim
            row[2].text = L.typo
            row[3].text = L.perf
            row[4].text = str(int(L.qte))
            row[5].text = L.pose
            row[6].text = (L.commentaire or "").strip()

        # 5h) Style & espacement
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





