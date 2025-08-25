def analyze(docstore: dict) -> dict:
    text = docstore["doc_text"]
    results = {
        "Variantes": "Non detecte",
        "Criteres": "Non detecte",
        "Delais": "Non detecte",
        "Penalites": "Non detecte",
        "Prix": "Non detecte",
        "Assurances": "Non detecte",
        "SAV": "Non detecte",
        "Pieges": []
    }

    if "variante" in text.lower(): results["Variantes"] = "Mentionne"
    if "penalite" in text.lower(): results["Penalites"] = "Penalites prevues"

    return results
