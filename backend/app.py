"""Lightweight Render web runtime; private model inference runs on the client.

For real custom CSV predictions, run this locally with TABPFN_MODE=local.
The public free deployment serves audited recorded TabPFN artifacts.
"""
from pathlib import Path
import json
import os
import threading
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from ml.policy import decide

ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title="Stillroot",version="1.0.0")
origins=os.getenv("ALLOWED_ORIGINS","http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET","POST"],allow_headers=["Content-Type"])
lock=threading.Lock()

@app.middleware("http")
async def headers(request: Request,call_next):
    try:
        declared_length=int(request.headers.get("content-length","0"))
    except ValueError:
        return JSONResponse({"detail":"Invalid Content-Length"},status_code=400)
    if declared_length>200000:
        return JSONResponse({"detail":"Request is too large"},status_code=413)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    return response

@app.get("/api/health")
def health():
    return {"status":"ok","version":"1.0.0","tabpfn_mode":os.getenv("TABPFN_MODE","recorded"),
        "gemma":"browser-local","forecast_artifact":(ROOT/"web/public/data/forecasts.json").is_file()}

class Signal(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra="forbid")
    moisture:float=Field(ge=0,le=100)
    lower:float=Field(ge=0,le=100)
    away_days:int=Field(ge=0,le=7)
    stale:bool=False

@app.post("/api/signal")
def signal(body:Signal):
    return {"action":decide(body.moisture,body.lower,body.away_days,body.stale),"source":"inspectable_policy"}

class HistoryRow(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra="ignore")
    moisture:float=Field(ge=0,le=100)
    temperature:float=Field(ge=0,le=60)
    humidity:float=Field(ge=0,le=100)
    light_hours:float=Field(ge=0,le=24)
    pot_size:float=Field(gt=0,le=100)
    days_since_water:float=Field(ge=0,le=365)
    next_moisture:float=Field(ge=0,le=100)

class ForecastRequest(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra="forbid")
    rows:list[HistoryRow]=Field(min_length=20,max_length=1000)
    current:float=Field(ge=0,le=100)
    temperature:float=Field(ge=0,le=60)
    humidity:float=Field(ge=0,le=100)
    light_hours:float=Field(ge=0,le=24)
    pot_size:float=Field(gt=0,le=100)

@app.post("/api/forecast")
def forecast(body:ForecastRequest):
    if os.getenv("TABPFN_MODE","recorded")!="local":
        raise HTTPException(503,"This free hosted demo uses recorded TabPFN predictions. Run the local runtime with TABPFN_MODE=local for your CSV.")
    if not lock.acquire(blocking=False):
        raise HTTPException(429,"Another local forecast is running; please try again shortly.")
    try:
        import numpy as np
        import pandas as pd
        import torch
        from ml.forecast import new_model
        from ml.make_data import FEATURES
        torch.set_num_threads(4)
        df=pd.DataFrame([r.model_dump() for r in body.rows])
        model=new_model()
        model.fit(df[FEATURES],df.next_moisture)
        value=body.current
        points=[{"day":0,"mean":value,"lower":value,"upper":value}]
        for day in range(1,8):
            x=pd.DataFrame([[value,body.temperature,body.humidity,body.light_hours,body.pot_size,day]],columns=FEATURES)
            value=float(np.clip(model.predict(x)[0],0,100))
            # Explicit heuristic. No calibration claims for arbitrary uploads.
            width=3*np.sqrt(day)
            points.append({"day":day,"mean":value,"lower":max(0,value-width),"upper":min(100,value+width)})
        return {"source":"live_local_tabpfn","points":points,"interval_note":"Uncalibrated heuristic interval for custom history"}
    finally:
        lock.release()

static=ROOT/"dist"
if static.is_dir():
    app.mount("/",StaticFiles(directory=static,html=True),name="web")
