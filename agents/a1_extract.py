import os, uuid, zipfile, requests, pdfplumber, docx, pandas as pd

def download_and_extract(url, upload_dir):
    job_id = str(uuid.uuid4())
    local_zip = os.path.join(upload_dir, f"{job_id}.zip")
    extract_dir = os.path.join(upload_dir, job_id)
    os.makedirs(extract_dir, exist_ok=True)

    r = requests.get(url, stream=True)
    with open(local_zip, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    with zipfile.ZipFile(local_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    return job_id, os.listdir(extract_dir)

def read_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def read_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt: text += txt + "\n"
    return text

def read_excel(path):
    df = pd.read_excel(path)
    return df.to_dict(orient="records")

def build_docstore(job_id, upload_dir="uploads"):
    path = os.path.join(upload_dir, job_id)
    doc_text, tables = "", []
    files = []

    for file in os.listdir(path):
        fpath = os.path.join(path, file)
        files.append(file)
        if file.endswith(".docx"):
            doc_text += read_docx(fpath) + "\n"
        elif file.endswith(".pdf"):
            doc_text += read_pdf(fpath) + "\n"
        elif file.endswith(".xlsx"):
            tables.extend(read_excel(fpath))

    return {"files": files, "doc_text": doc_text, "tables": tables}
