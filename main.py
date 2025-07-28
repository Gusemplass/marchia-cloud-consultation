from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
from utils.extract_zip import extract_zip_content
from utils.parse_cctp import extract_cctp_data
from utils.parse_dpgf import parse_dpgf_excel
from utils.extract_visuels import extract_images_from_pdf
from utils.generate_word import generate_consultation_doc

app = FastAPI()  # ← C’est CET objet que Render ne trouvait pas

@app.post("/upload")
async def upload_zip(zip_file: UploadFile = File(...)):
    upload_dir = "temp"
    os.makedirs(upload_dir, exist_ok=True)

    zip_path = os.path.join(upload_dir, "input.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)

    extract_zip_content(zip_path, upload_dir)

    cctp_data = extract_cctp_data(upload_dir)
    dpgf_data = parse_dpgf_excel(upload_dir)
    visuel_paths = extract_images_from_pdf(upload_dir)

    output_path = "fiche_consultation_output.docx"
    generate_consultation_doc(
        template_path="model/ddp_GMMARCH-IAV2.docx",
        output_path=output_path,
        chantier=cctp_data["chantier"],
        descriptif=cctp_data["descriptif"],
        tableau=dpgf_data,
        visuels=visuel_paths
    )

    return FileResponse(output_path, filename="fiche_consultation.docx")# Entrypoint FastAPI
