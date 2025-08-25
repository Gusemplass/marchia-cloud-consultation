def analyze(docstore: dict) -> dict:
    text = docstore["doc_text"]
    results = {
        "Materiaux_amiante": [],
        "Modes_operatoires": [],
        "Impacts": {},
        "Vigilances": []
    }

    if "amiante" in text.lower():
        results["Materiaux_amiante"].append({"Element":"Joint", "Localisation":"Non precise"})
        results["Modes_operatoires"].append({"Element":"Joint","Intervention":"Sous-section 4"})
        results["Vigilances"].append("Surveiller coactivite")

    return results
