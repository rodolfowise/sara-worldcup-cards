"""
API FastAPI — Figurinhas da Copa
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import db

app = FastAPI(title="Figurinhas da Copa")

# Inicializa banco na subida
db.init_db()

# ── Servir frontend estático ──────────────────────────────────────────────────
WWW = os.path.join(os.path.dirname(__file__), "..", "www")
app.mount("/static", StaticFiles(directory=WWW), name="static")

@app.get("/", response_class=FileResponse)
def root():
    return FileResponse(os.path.join(WWW, "index.html"))

@app.get("/sw.js", response_class=FileResponse)
def sw():
    return FileResponse(os.path.join(WWW, "sw.js"))

@app.get("/manifest.json", response_class=FileResponse)
def manifest():
    return FileResponse(os.path.join(WWW, "manifest.json"))


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/paises")
def paises():
    return db.listar_paises()


@app.get("/api/resumo")
def resumo():
    return db.resumo()


@app.get("/api/busca")
def busca(sigla: str, numero: int):
    fig = db.buscar_figurinha(sigla, numero)
    if not fig:
        raise HTTPException(404, detail="Figurinha não encontrada no catálogo.")
    return fig


@app.get("/api/pais/{sigla}")
def pais(sigla: str):
    rows = db.listar_pais(sigla)
    if not rows:
        raise HTTPException(404, detail="País não encontrado.")
    return rows


@app.get("/api/repetidas")
def repetidas():
    return db.listar_repetidas()


@app.get("/api/faltando")
def faltando():
    return db.listar_faltando()


class IncluirBody(BaseModel):
    figurinha_id: int

@app.post("/api/incluir")
def incluir(body: IncluirBody):
    qtd = db.incluir_figurinha(body.figurinha_id)
    return {"ok": True, "quantidade": qtd}


class ExcluirBody(BaseModel):
    figurinha_id: int

@app.post("/api/excluir-repetida")
def excluir_repetida(body: ExcluirBody):
    qtd = db.excluir_repetida(body.figurinha_id)
    return {"ok": True, "quantidade": qtd}


class TrocaBody(BaseModel):
    entregue_id: int
    recebida_id: int

@app.post("/api/trocar")
def trocar(body: TrocaBody):
    db.registrar_troca(body.entregue_id, body.recebida_id)
    return {"ok": True}
