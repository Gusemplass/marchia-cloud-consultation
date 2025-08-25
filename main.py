# -*- coding: utf-8 -*-
import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import des agents
from agents import (
    a1_extract,
    a2_cctp,
    a3_plans,
    a4_rc_ccap,
    a5_dpgf,
    a6_livrables,
    a7_amiante
)

app = FastAPI(title="LucidIA – Multi-Agents DCE")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------- MODELE REPONSE --------
class JobResponse(BaseModel):
    job_id: str
    status: str
    files: list

# -------- 1. UPLOAD --------
@app.post("/upload-url", response_model=JobResponse)
def upload_url(file_url: str):
    """Télécharge un ZIP depuis une URL, l'extrait, retourne job_id + liste fichiers"""
    job_id, files = a1_extract.download_and_extract(file_url, UPLOAD_DIR)
    return {"job_id": job_id, "status": "uploaded", "files": files}

# -------- 2. ANALYSE (ASYNC) --------
@app.post("/analyze/{job_id}")
async def analyze_job(job_id: str):
    """Orchestre A2–A5 (+A7 si amiante), puis lance A6"""
    docstore = a1_extract.build_docstore(job_id, upload_dir=UPLOAD_DIR)

    # Création des tâches en parallèle
    tasks = [
        asyncio.create_task(async_analyze(a2_cctp.analyze, docstore, "CCTP")),
        asyncio.create_task(async_analyze(a3_plans.analyze, docstore, "Plans")),
        asyncio.create_task(async_analyze(a4_rc_ccap.analyze, docstore, "RC_CCAP")),
        asyncio.create_task(async_analyze(a5_dpgf.analyze, docstore, "DPGF")),
    ]

    # Ajouter A7 Amiante si pertinent
    if "amiante" in " ".join(docstore["files"]).lower() or "amiante" in docstore["doc_text"].lower():
        tasks.append(asyncio.create_task(async_analyze(a7_amiante.analyze, docstore, "Amiante")))

    # Exécution parallèle
    results_list = await asyncio.gather(*tasks)

    # Fusion résultats
    results = {}
    for r in results_list:
        results.update(r)

    # Consolidation livrables
    livrables = a6_livrables.generate(results, job_id, upload_dir=UPLOAD_DIR)

    return {"job_id": job_id, "results": results, "livrables": livrables}

# -------- 3. RESULT --------
@app.get("/jobs/{job_id}/result")
def get_result(job_id: str):
    """Retourne le contenu final JSON (livrables, liens Word/Notion)"""
    path = os.path.join(UPLOAD_DIR, job_id, "result.json")
    if not os.path.exists(path):
        raise HTTPException(404, "Resultat non trouvé")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# -------- UTILITAIRE --------
async def async_analyze(func, docstore, label):
    """Wrapper async pour exécuter un agent"""
    try:
        res = func(docstore)
        return {label: res}
    except Exception as e:
        return {label: {"error": str(e)}}
