import json, os

def generate(results: dict, job_id: str, upload_dir="uploads") -> dict:
    result_path = os.path.join(upload_dir, job_id, "result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Ici tu pourras générer ton Word (fiche_demo_MARCHIA_full.docx)
    # via python-docx en insérant results["CCTP"], results["DPGF"], etc.

    return {"result_json": result_path, "word_fiche": "todo.docx"}
