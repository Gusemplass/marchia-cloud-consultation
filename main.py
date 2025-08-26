from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

__VERSION__ = "2025-08-26-3"  # <— bump version pour vérifier
TEMPLATE_PATH = "templates/fiche_demo_MARCHIA_full.docx"

app = FastAPI()

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

def find_paragraph(doc: Document, needles: List[str]) -> Optional[Paragraph]:
    for p in doc.paragraphs:
        for n in needles:
            if n in p.text:
                return p
    return None

def block_items(doc: Document):
    """Itère paragraphes et tableaux dans l'ordre d'apparition."""
    body = doc._element.body
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)

@app.get("/")
def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !", "version": __VERSION__}

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement ✅", "data": req.model_dump()}

    doc = Document(TEMPLATE_PATH)

    # Remplacement simple dans le corps (si tu as {{projet}} etc.)
    for p in doc.paragraphs:
        if "{{projet}}" in p.text: p.text = p.text.replace("{{projet}}", req.projet)
        if "{{moa}}" in p.text:    p.text = p.text.replace("{{moa}}", req.moa)
        if "{{lot}}" in p.text:    p.text = p.text.replace("{{lot}}", req.lot)

    # Descriptif : accepte [[...]] OU {{...}}
    p_desc = find_paragraph(doc, ["[[DESCRIPTIF_CCTP]]", "{{DESCRIPTIF_CCTP}}"])
    if p_desc:
        p_desc.text = req.descriptif

    # Tableau : essaie de remplir celui qui se trouve juste après le marqueur.
    p_tbl = find_paragraph(doc, ["[[TABLEAU_QUANTITATIF]]", "{{TABLEAU_QUANTITATIF}}"])
    if req.lignes and p_tbl:
        # 1) Efface le texte du marqueur
        marker_texts = ["[[TABLEAU_QUANTITATIF]]", "{{TABLEAU_QUANTITATIF}}"]
        for m in marker_texts:
            if m in p_tbl.text:
                p_tbl.text = p_tbl.text.replace(m, "").strip()

        # 2) Cherche le "prochain bloc" après ce paragraphe : si c'est un Table, on le remplit
        items = list(block_items(doc))
        # trouve l'index du paragraphe
        try:
            idx = next(i for i, it in enumerate(items) if isinstance(it, Paragraph) and it._p is p_tbl._p)
        except StopIteration:
            idx = None

        dest_table: Optional[Table] = None
        if idx is not None:
            # cherche le tableau suivant
            for it in items[idx+1:]:
                if isinstance(it, Table):
                    dest_table = it
                    break

        if dest_table is None:
            # pas de tableau après le marqueur → on en crée un et on l'insère "ici"
            dest_table = doc.add_table(rows=1, cols=7)
            hdr = dest_table.rows[0].cells
            hdr[0].text = "Rép."; hdr[1].text = "Dim."; hdr[2].text = "Typo."
            hdr[3].text = "Perf."; hdr[4].text = "Qté"; hdr[5].text = "Pose"; hdr[6].text = "Commentaire"
            p_tbl._p.addnext(dest_table._tbl)
        else:
            # s'il existe déjà un header dans ton modèle, on peut l'écraser/laisser tel quel.
            pass

        # 3) Ajoute les lignes
        for L in req.lignes:
            row = dest_table.add_row().cells
            row[0].text = L.rep
            row[1].text = L.dim
            row[2].text = L.typo
            row[3].text = L.perf
            row[4].text = str(L.qte)
            row[5].text = L.pose
            row[6].text = (L.commentaire or "").strip()

        # (option) style de tableau si souhaité
        try:
            dest_table.style = "Table Grid"
        except Exception:
            pass

    # Retour docx
    buf = BytesIO()
    doc.save(buf)
    content = buf.getvalue()
    filename = f'fiche_{req.projet.replace(" ", "_")}.docx'
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )





