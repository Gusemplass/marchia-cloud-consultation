# ⬆️ AJOUTE ces imports en haut
from docx.enum.text import WD_BREAK
from docx.shared import Pt

# … (le reste inchangé)

__VERSION__ = "2025-08-26-4"  # bump version pour contrôle

# Helpers (garde ceux que tu as déjà si présents)
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

def find_paragraph(doc: Document, needles):
    for p in doc.paragraphs:
        if any(n in p.text for n in needles):
            return p
    return None

def block_items(doc: Document):
    """Paragraphes et tableaux dans l'ordre d'apparition."""
    body = doc._element.body
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)

def clear_table_body_keep_header(table: Table):
    """Supprime toutes les lignes sauf la première (header)."""
    while len(table.rows) > 1:
        table._tbl.remove(table.rows[1]._tr)

@app.post("/genere-fiche")
def genere_fiche(req: FicheRequest, format: str = Query("docx", pattern="^(docx|json)$")):
    if format == "json":
        return {"status": "ok", "message": "Fiche reçue correctement ✅", "data": req.model_dump()}

    doc = Document(TEMPLATE_PATH)

    # Calibri 11 partout (style Normal)
    try:
        normal = doc.styles['Normal']
        normal.font.name = 'Calibri'
        normal.font.size = Pt(11)
    except Exception:
        pass

    # Remplacements simples (si tu as {{projet}} etc.)
    for p in doc.paragraphs:
        if "{{projet}}" in p.text: p.text = p.text.replace("{{projet}}", req.projet)
        if "{{moa}}" in p.text:    p.text = p.text.replace("{{moa}}", req.moa)
        if "{{lot}}" in p.text:    p.text = p.text.replace("{{lot}}", req.lot)

    # Descriptif au marqueur (accepte [[...]] ou {{...}})
    p_desc = find_paragraph(doc, ["[[DESCRIPTIF_CCTP]]", "{{DESCRIPTIF_CCTP}}"])
    if p_desc:
        p_desc.text = req.descriptif

    # Tableau au marqueur
    p_tbl = find_paragraph(doc, ["[[TABLEAU_QUANTITATIF]]", "{{TABLEAU_QUANTITATIF}}"])
    dest_table = None
    if p_tbl and req.lignes:
        # Effacer le texte du marqueur et insérer un SAUT DE PAGE (page 2 garantie)
        p_tbl.text = ""
        run = p_tbl.add_run()
        run.add_break(WD_BREAK.PAGE)

        # Cherche le premier tableau après le marqueur (si déjà présent dans le modèle)
        items = list(block_items(doc))
        try:
            idx = next(i for i, it in enumerate(items) if isinstance(it, Paragraph) and it._p is p_tbl._p)
        except StopIteration:
            idx = None

        if idx is not None:
            for it in items[idx+1:]:
                if isinstance(it, Table):
                    dest_table = it
                    break

        # Si pas de tableau existant → on en crée un propre avec entête
        if dest_table is None:
            dest_table = doc.add_table(rows=1, cols=7)
            hdr = dest_table.rows[0].cells
            hdr[0].text = "Rép."
            hdr[1].text = "Dim."
            hdr[2].text = "Typo."
            hdr[3].text = "Perf. (Uw / Rw+Ctr)"
            hdr[4].text = "Qté"
            hdr[5].text = "Pose"
            hdr[6].text = "Commentaire"
            # Insère le tableau juste après le paragraphe-marqueur
            p_tbl._p.addnext(dest_table._tbl)
        else:
            # Nettoie les lignes vides héritées du modèle
            clear_table_body_keep_header(dest_table)
            # Harmonise les entêtes si besoin
            hdr = dest_table.rows[0].cells
            headers = ["Rép.", "Dim.", "Typo.", "Perf. (Uw / Rw+Ctr)", "Qté", "Pose", "Commentaire"]
            for i, h in enumerate(headers[:len(hdr)]):
                hdr[i].text = h

        # Remplissage des lignes
        for L in req.lignes:
            row = dest_table.add_row().cells
            row[0].text = L.rep
            row[1].text = L.dim
            row[2].text = L.typo
            row[3].text = L.perf
            row[4].text = str(L.qte)
            row[5].text = L.pose
            row[6].text = (L.commentaire or "").strip()

        # Style de tableau lisible
        try:
            dest_table.style = "Table Grid"
        except Exception:
            pass

    # Export
    buf = BytesIO(); doc.save(buf); content = buf.getvalue()
    filename = f'fiche_{req.projet.replace(" ", "_")}.docx'
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )






