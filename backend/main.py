import os
from fastapi import FastAPI, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from chat import process_query, get_history
from uploader import handle_upload
from prom_query import query_time_series
from database import SessionLocal, engine, Base
from k8s_client import (
    list_pods, list_deployments, list_services,
    list_configmaps, list_namespaces, list_nodes
)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize DB
Base.metadata.create_all(bind=engine)

# App init
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

# --- Endpoints ---

@app.get("/")
def root():
    return {"message": "LLM-powered Kubernetes Assistant is running."}

@app.post("/ask")
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    return process_query(request.query, db)

@app.get("/history")
def fetch_history(db: Session = Depends(get_db)):
    return get_history(db)

@app.post("/upload")
def upload_yaml(file: UploadFile = File(...)):
    return handle_upload(file)

# Unified Prometheus time-series endpoint
@app.get("/metrics/time-series")
def get_time_series(metric_type: str = Query(...)):
    return query_time_series(metric_type)

# Kubernetes resource APIs
@app.get("/pods")
def get_pods():
    return list_pods()

@app.get("/deployments")
def get_deployments():
    return list_deployments()

@app.get("/services")
def get_services():
    return list_services()

@app.get("/configmaps")
def get_configmaps():
    return list_configmaps()

@app.get("/namespaces")
def get_namespaces():
    return list_namespaces()

@app.get("/nodes")
def get_nodes():
    return list_nodes()
