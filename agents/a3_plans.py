def analyze(docstore: dict) -> dict:
    text = docstore["doc_text"]
    results = {
        "Facades": "Non detecte",
        "Acces": "Non detecte",
        "Phasage": "Non detecte",
        "Environnement": "Non detecte",
        "Quantitatif": "Non detecte"
    }

    if "nacelle" in text.lower(): results["Acces"] = "Nacelle necessaire"
    if "echafaudage" in text.lower(): results["Acces"] = "Echafaudage necessaire"
    if "site occupe" in text.lower(): results["Phasage"] = "Site occupe"

    return results
