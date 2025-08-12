# server.py
import sys, os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, Header, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd

# importa seu código
sys.path.append(".")
from rascunho import (
    executar_consulta,
    consulta_amostra,
    consulta_resumo,
    consulta_distribuicao,
)

load_dotenv()

API_KEY = os.getenv("API_KEY", "")  # opcional (defina no .env, ex.: API_KEY=segreta123)

def check_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

class AskIn(BaseModel):
    pergunta: str
    limit: Optional[int] = 50

class Resposta(BaseModel):
    answer: str
    sample: Optional[List[Dict[str, Any]]] = None

app = FastAPI(title="Chat Rondas API", version="1.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ask", response_model=Resposta)
def ask(payload: AskIn, auth: bool = Depends(check_key)):
    # resposta textual (usa sua função atual)
    answer = executar_consulta(payload.pergunta)

    # amostra opcional (tolerante a erro)
    sample_json: List[Dict[str, Any]] = []
    try:
        df = consulta_amostra(payload.pergunta, limit=payload.limit or 50)
        # NaN -> None para JSON
        sample_json = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")
    except Exception:
        sample_json = []
    return Resposta(answer=answer, sample=sample_json)

@app.get("/resumo")
def resumo(pergunta: str, auth: bool = Depends(check_key)):
    df = consulta_resumo(pergunta)
    return JSONResponse(df.to_dict(orient="records"))

@app.get("/distribuicao")
def distribuicao(pergunta: str, auth: bool = Depends(check_key)):
    df = consulta_distribuicao(pergunta)
    return JSONResponse(df.to_dict(orient="records"))

@app.get("/amostra")
def amostra(pergunta: str, limit: int = 100, auth: bool = Depends(check_key)):
    df = consulta_amostra(pergunta, limit=limit)
    return JSONResponse(df.to_dict(orient="records"))

# Form POST simples (para integração sem JSON)
@app.post("/ask-form", response_model=Resposta)
def ask_form(q: str = Form(...), limit: int = Form(50), auth: bool = Depends(check_key)):
    answer = executar_consulta(q)
    sample_json: List[Dict[str, Any]] = []
    try:
        df = consulta_amostra(q, limit=limit)
        sample_json = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")
    except Exception:
        sample_json = []
    return Resposta(answer=answer, sample=sample_json)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8025)  # <-- porta alterada
