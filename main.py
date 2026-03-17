from fastapi import FastAPI
from agent import run_agent
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/autobook")
def autobook(date: str, preference: str):
    result = run_agent(
        date=date,
        preference=preference,
        email=os.getenv("PITCHPRO_EMAIL"),
        password=os.getenv("PITCHPRO_PASSWORD")
    )
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)