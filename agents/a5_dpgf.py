def analyze(docstore: dict) -> dict:
    tables = docstore["tables"]
    results = {"Tableau": [], "Manques": []}

    for row in tables:
        item = row.get("Designation") or row.get("Item") or "Inconnu"
        qte = row.get("Qte") or row.get("Quantite") or 0
        unite = row.get("Unite") or "U"
        results["Tableau"].append({"Item": item, "Qte": qte, "Unite": unite})

    return results
