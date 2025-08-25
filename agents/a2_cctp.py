def analyze(docstore: dict) -> dict:
    text = docstore["doc_text"]
    results = {"Matieres": [], "Performances": {}, "Normes": [], "Accessoires": []}

    if "PVC" in text: results["Matieres"].append("PVC")
    if "Uw" in text: results["Performances"]["Uw"] = "detected"
    if "DTU 36.5" in text: results["Normes"].append("DTU 36.5")

    return results
