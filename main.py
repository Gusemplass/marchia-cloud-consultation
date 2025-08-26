from fastapi import FastAPI

# Création de l'app FastAPI
app = FastAPI()

# Endpoint racine pour tester
@app.get("/")
async def root():
    return {"message": "🚀 Marchia Cloud Consultation en ligne !"}
