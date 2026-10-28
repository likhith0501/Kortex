import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import BASE_DIR, PAPERS_DIR, REPORTS_DIR, OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL
from backend.database import init_db, get_connection
from backend.schemas import (
    PaperResponse, PaperAnalysisResponse, HealthResponse,
    RecommendationItem, GraphResponse, ResearchGapItem,
    ComparisonRequest, ComparisonMatrixResponse, SettingsModel,
    JobProgressResponse, ReportRequest
)
from backend.services.pdf_service import extract_pdf_data, compute_file_hash
from backend.services.embedding_service import compute_embedding, get_active_model_name
from backend.services.ollama_service import check_ollama_status
from backend.services.analysis_service import analyze_paper
from backend.services.recommendation_service import get_recommendations_for_paper, build_similarity_graph
from backend.services.comparison_service import generate_comparison_matrix, export_comparison_to_csv
from backend.services.gap_service import get_session_gaps, discover_research_gaps
from backend.services.report_service import generate_session_report
from backend.sample_data.sample_papers import load_sample_papers_into_session

app = FastAPI(
    title="Kortex API",
    description="Autonomous Research Intelligence API",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

# --- Health Endpoint ---
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM papers")
    total_papers = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM chunks")
    total_chunks = cursor.fetchone()["count"]
    
    # Check Ollama
    ollama_ok, models = await check_ollama_status()
    active_model = f"Ollama: {models[0]}" if (ollama_ok and models) else "Extractive Engine (Ollama Offline)"
    conn.close()
    
    return {
        "api_status": "ok",
        "ollama_available": ollama_ok,
        "active_model_name": active_model,
        "embedding_model_loaded": get_active_model_name(),
        "sqlite_status": "connected",
        "total_papers": total_papers,
        "total_chunks": total_chunks
    }

# --- Settings ---
@app.get("/api/settings", response_model=SettingsModel)
async def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = dict(cursor.fetchall())
    conn.close()
    return {
        "ollama_url": rows.get("ollama_url", "http://localhost:11434"),
        "ollama_model": rows.get("ollama_model", "llama3.2"),
        "use_ollama": rows.get("use_ollama", "true").lower() == "true",
        "embedding_mode": rows.get("embedding_mode", "local_vectorizer")
    }

@app.put("/api/settings", response_model=SettingsModel)
async def update_settings(settings: SettingsModel):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ollama_url', ?)", (settings.ollama_url,))
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ollama_model', ?)", (settings.ollama_model,))
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('use_ollama', ?)", (str(settings.use_ollama).lower(),))
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('embedding_mode', ?)", (settings.embedding_mode,))
    conn.commit()
    conn.close()
    return settings

# --- Jobs / Background Progress ---
@app.get("/api/jobs/{job_id}", response_model=JobProgressResponse)
async def get_job_progress(job_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    conn.close()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(job)

def update_job_status(job_id: str, stage: str, progress: int, status: str, error: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE jobs 
        SET stage = ?, progress = ?, status = ?, error = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (stage, progress, status, error, job_id)
    )
    conn.commit()
    conn.close()

# --- Paper Pipeline Worker ---
async def process_paper_pipeline(job_id: str, paper_id: str, session_id: str, file_path: Path):
    try:
        # Step 1: Parsing
        update_job_status(job_id, "Parsing PDF Structure", 25, "running")
        extracted = extract_pdf_data(file_path)
        
        # Update paper metadata
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE papers 
            SET title = ?, authors = ?, year = ?, abstract = ?, page_count = ?, status = 'processing'
            WHERE id = ?
            """,
            (extracted["title"], extracted["authors"], extracted["year"], extracted["abstract"], extracted["page_count"], paper_id)
        )
        conn.commit()
        
        # Step 2: Chunking & Step 3: Embedding (Optimized Batch)
        update_job_status(job_id, "Section Chunking & Embedding", 65, "running")
        chunk_records = []
        for c in extracted["chunks"]:
            chunk_id = f"chk_{uuid.uuid4().hex[:10]}"
            emb_json = compute_embedding(c["text"])
            chunk_records.append((chunk_id, paper_id, c["section"], c["page"], c["text"], emb_json, c["chunk_index"]))

        cursor.executemany(
            """
            INSERT INTO chunks (id, paper_id, section, page, text, embedding, chunk_index)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            chunk_records
        )
        conn.commit()
        
        # Step 4: Analyzing & Citations
        update_job_status(job_id, "Synthesizing Evidence-Backed Analysis", 90, "running")
        analysis = await analyze_paper(extracted["title"], extracted["abstract"], extracted["chunks"])
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO analyses (
                id, paper_id, summary, problem, method, dataset, metrics, results, contributions, limitations, future_work, source_label, evidence_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                f"ana_{paper_id}",
                paper_id,
                analysis["summary"],
                analysis["problem"],
                analysis["method"],
                analysis["dataset"],
                analysis["metrics"],
                analysis["results"],
                analysis["contributions"],
                analysis["limitations"],
                analysis["future_work"],
                analysis["source_label"],
                json.dumps(analysis["evidence"])
            )
        )
        cursor.execute("UPDATE papers SET status = 'ready' WHERE id = ?", (paper_id,))
        conn.commit()
        conn.close()
        
        # Refresh Gaps across session
        discover_research_gaps(session_id)
        
        update_job_status(job_id, "Complete", 100, "completed")
    except Exception as e:
        update_job_status(job_id, "Failed", 100, "failed", str(e))
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE papers SET status = 'failed' WHERE id = ?", (paper_id,))
        conn.commit()
        conn.close()

# --- Paper Endpoints ---
@app.post("/api/papers/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form("default")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum 50MB limit.")
        
    file_hash = compute_file_hash(file_bytes)
    
    conn = get_connection()
    cursor = conn.cursor()
    # Check duplicate
    cursor.execute("SELECT id, title, status FROM papers WHERE hash = ? AND session_id = ?", (file_hash, session_id))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return {
            "paper_id": existing["id"],
            "title": existing["title"],
            "status": "duplicate",
            "message": "Duplicate paper already exists in this research session."
        }
        
    paper_id = f"paper_{uuid.uuid4().hex[:8]}"
    file_path = PAPERS_DIR / f"{paper_id}.pdf"
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    cursor.execute(
        """
        INSERT INTO papers (id, session_id, hash, filename, file_path, title, status, file_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'parsing', ?, datetime('now'))
        """,
        (paper_id, session_id, file_hash, file.filename, str(file_path), file.filename, len(file_bytes))
    )
    
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    cursor.execute(
        """
        INSERT INTO jobs (id, paper_id, stage, progress, status, updated_at)
        VALUES (?, ?, 'Parsing PDF Structure', 10, 'running', datetime('now'))
        """,
        (job_id, paper_id)
    )
    conn.commit()
    conn.close()
    
    background_tasks.add_task(process_paper_pipeline, job_id, paper_id, session_id, file_path)
    
    return {
        "job_id": job_id,
        "paper_id": paper_id,
        "filename": file.filename,
        "status": "processing"
    }

@app.get("/api/papers", response_model=List[PaperResponse])
async def list_papers(session_id: str = "default"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
    rows = cursor.fetchall()
    
    result = []
    for r in rows:
        paper_dict = dict(r)
        # Fetch analysis if available
        cursor.execute("SELECT * FROM analyses WHERE paper_id = ?", (r["id"],))
        ana_row = cursor.fetchone()
        if ana_row:
            ana_dict = dict(ana_row)
            try:
                ana_dict["evidence"] = json.loads(ana_dict.get("evidence_json", "{}"))
            except Exception:
                ana_dict["evidence"] = {}
            paper_dict["analysis"] = ana_dict
        else:
            paper_dict["analysis"] = None
        result.append(paper_dict)
        
    conn.close()
    return result

@app.get("/api/papers/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        raise HTTPException(status_code=404, detail="Paper not found")
        
    paper_dict = dict(r)
    cursor.execute("SELECT * FROM analyses WHERE paper_id = ?", (paper_id,))
    ana_row = cursor.fetchone()
    if ana_row:
        ana_dict = dict(ana_row)
        try:
            ana_dict["evidence"] = json.loads(ana_dict.get("evidence_json", "{}"))
        except Exception:
            ana_dict["evidence"] = {}
        paper_dict["analysis"] = ana_dict
    else:
        paper_dict["analysis"] = None
        
    conn.close()
    return paper_dict

@app.delete("/api/papers/{paper_id}")
async def delete_paper(paper_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, file_path FROM papers WHERE id = ?", (paper_id,))
    p = cursor.fetchone()
    if not p:
        conn.close()
        raise HTTPException(status_code=404, detail="Paper not found")
        
    session_id = p["session_id"]
    cursor.execute("DELETE FROM chunks WHERE paper_id = ?", (paper_id,))
    cursor.execute("DELETE FROM analyses WHERE paper_id = ?", (paper_id,))
    cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()
    
    # Recalculate gaps
    discover_research_gaps(session_id)
    return {"status": "deleted", "paper_id": paper_id}

@app.get("/api/papers/{paper_id}/file")
async def get_paper_file(paper_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, filename FROM papers WHERE id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
        
    return FileResponse(
        row["file_path"],
        media_type="application/pdf",
        filename=row["filename"],
        headers={"Content-Disposition": f'inline; filename="{row["filename"]}"'}
    )

@app.post("/api/papers/{paper_id}/analyze")
async def reanalyze_paper(paper_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, abstract, session_id FROM papers WHERE id = ?", (paper_id,))
    p = cursor.fetchone()
    if not p:
        conn.close()
        raise HTTPException(status_code=404, detail="Paper not found")
        
    cursor.execute("SELECT section, page, text, chunk_index FROM chunks WHERE paper_id = ? ORDER BY chunk_index", (paper_id,))
    chunks = [dict(c) for c in cursor.fetchall()]
    conn.close()
    
    analysis = await analyze_paper(p["title"], p["abstract"], chunks)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO analyses (
            id, paper_id, summary, problem, method, dataset, metrics, results, contributions, limitations, future_work, source_label, evidence_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            f"ana_{paper_id}",
            paper_id,
            analysis["summary"],
            analysis["problem"],
            analysis["method"],
            analysis["dataset"],
            analysis["metrics"],
            analysis["results"],
            analysis["contributions"],
            analysis["limitations"],
            analysis["future_work"],
            analysis["source_label"],
            json.dumps(analysis["evidence"])
        )
    )
    conn.commit()
    conn.close()
    
    discover_research_gaps(p["session_id"])
    return analysis

# --- Sample Papers Loader ---
@app.post("/api/papers/sample")
async def load_sample_dataset(session_id: str = "default"):
    loaded = await load_sample_papers_into_session(session_id)
    return {
        "status": "success",
        "message": f"Successfully loaded and analyzed {len(loaded)} landmark research papers with full citation grounding.",
        "paper_ids": loaded
    }

# --- Recommendations & Graph ---
@app.get("/api/recommendations/{paper_id}", response_model=List[RecommendationItem])
async def get_recommendations(paper_id: str, session_id: str = "default", top_k: int = 5):
    return get_recommendations_for_paper(paper_id, session_id, top_k)

@app.get("/api/graph", response_model=GraphResponse)
async def get_graph(session_id: str = "default"):
    return build_similarity_graph(session_id)

# --- Comparison Workspace ---
@app.post("/api/compare", response_model=ComparisonMatrixResponse)
async def compare_papers(req: ComparisonRequest):
    if len(req.paper_ids) < 2:
        raise HTTPException(status_code=400, detail="Please select at least 2 papers to compare.")
    matrix_data = generate_comparison_matrix(req.session_id, req.paper_ids)
    matrix_data["csv_download_url"] = f"/api/compare/export-csv?session_id={req.session_id}&pids={','.join(req.paper_ids)}"
    return matrix_data

@app.get("/api/compare/export-csv")
async def export_comparison_csv_endpoint(session_id: str = "default", pids: str = Query(...)):
    paper_ids = [pid.strip() for pid in pids.split(",") if pid.strip()]
    matrix_data = generate_comparison_matrix(session_id, paper_ids)
    csv_content = export_comparison_to_csv(matrix_data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="researchmate_comparison.csv"'}
    )

# --- Research Gaps ---
@app.get("/api/gaps", response_model=List[ResearchGapItem])
async def list_research_gaps(session_id: str = "default"):
    return get_session_gaps(session_id)

# --- Reports ---
@app.post("/api/reports")
async def create_report(req: ReportRequest):
    return generate_session_report(req.session_id, req.title or "Research Intelligence Synthesis Report", req.format)

@app.get("/api/reports/{filename}/download")
async def download_report_file(filename: str):
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    media_type = "application/pdf" if filename.endswith(".pdf") else "text/markdown"
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# --- Serve Frontend (React SPA) ---
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"detail": "Frontend not built. Run: cd frontend && npm run build"}
else:
    @app.get("/{full_path:path}")
    async def serve_spa_not_built(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        return {"detail": "Frontend not built. Run: cd frontend && npm run build"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
