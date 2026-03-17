from fastapi import FastAPI
import os
from agent import run_agent

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/autobook")
def autobook(date: str, preference: str):
    try:
        result = run_agent(
            date=date,
            preference=preference,
            email=os.getenv("PITCHPRO_EMAIL"),
            password=os.getenv("PITCHPRO_PASSWORD")
        )
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
