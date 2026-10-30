from fastapi import FastAPI

app = FastAPI(title="Surgical Item Finder")

@app.get("/health")
def health():
    return {"status": "ok"}
