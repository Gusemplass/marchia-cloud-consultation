#import pandas as pd
import os

def parse_dpgf_excel(folder):
    for file in os.listdir(folder):
        if file.endswith(".xlsx"):
            filepath = os.path.join(folder, file)
            try:
                df = pd.read_excel(filepath)
                return df.fillna("").to_dict(orient="records")
            except Exception as e:
                print(f"Erreur lecture DPGF : {e}")
    return [] Lecture DPGF
