import zipfile
import os

def extract_zip_content(zip_path, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)# Extraction et tri du zip
