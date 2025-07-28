import fitz  # PyMuPDF
import os

def extract_images_from_pdf(folder):
    visuels = []
    for file in os.listdir(folder):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder, file)
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                image_path = os.path.join(folder, f"visuel_{i}.png")
                pix = page.get_pixmap()
                pix.save(image_path)
                visuels.append(image_path)
            break  # On prend le premier PDF trouvé avec des visuels
    return visuels# Extraction visuels PDF
