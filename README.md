# KORTEX — Autonomous Research Intelligence
> **Tagline:** Upload. Understand. Discover What's Next.

Kortex is a calm, precise research cockpit designed for students, scientists, and applied researchers. It ingests research papers in PDF format, performs structured section-aware extraction, builds semantic knowledge graphs, compares methodologies across papers, and surfaces evidence-backed research gaps with exact page citations.

---

## Key Features

1. **Evidence-First AI & Visible Honesty:**
   - Every claim, summary, method, and limitation is paired with an interactive **Citation Chip** showing paper title, exact page number, and source quote.
   - Every AI-generated output displays a consistent **Source Badge** (`Extractive (no LLM)` or `Ollama: <model>`).
   - If Ollama is offline or unavailable, the system transparently falls back to heuristic section extraction, TF-IDF, and n-gram sentence ranking without fake progress or hallucinations.
2. **The Pipeline is the Hero:**
   - Real multi-stage processing stepper (`Parse PDF` → `Section Chunking` → `Vector Embedding` → `Analysis Synthesis`) driven by real backend status polling.
3. **Interactive Paper Similarity Graph:**
   - 2D force-directed knowledge topology mapping your library's papers and semantic connections with similarity scores and shared concept explanations.
4. **Multi-Paper Comparison Workspace:**
   - Side-by-side comparative matrix across 2 to 6 papers (Methodology, Datasets, Metrics, Empirical Results, Limitations).
   - Export directly to tabular CSV with one click.
5. **Evidence-Backed Research Gaps:**
   - Aggregated limitations and future-work directions across papers, clustered by semantic similarity, with confidence labels (**High / Medium / Low**) and rationales.
6. **Unified Synthesis Reports:**
   - Export full session research syntheses to Markdown (.md) or professional PDF (.pdf) documents.
7. **100% Offline & Free:**
   - Works entirely locally with zero paid API keys and no internet connection required after setup.

---

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (with CSS variables), Framer Motion, Lucide React, Zustand, React Router, Canvas-based Force Graph, Native PDF Reader.
- **Backend:** FastAPI, PyMuPDF (fitz), Scikit-Learn (TF-IDF & N-gram semantic vectorizer), Pandas, SQLite, optional Ollama LLM integration.

---

## Setup in Under 10 Steps

### Step 1: Clone or Navigate to the Repository
```bash
cd "agentic AI"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 4: (Optional) Set up Environment Variables
```bash
copy .env.example .env
```

### Step 5: Start the Application (One-Command)
**On Windows:**
Double-click or run:
```cmd
dev.bat
```

**On Linux / macOS:**
```bash
chmod +x dev.sh
./dev.sh
```

*(Alternatively, run backend: `python -m uvicorn backend.main:app --port 8000 --reload` and frontend: `cd frontend && npm run dev`)*

### Step 6: Open the Application
Open your browser to:
**http://localhost:5173**

### Step 7: Experience Landmark Research Instantly
In the top navigation bar, click **"Load Sample Papers"**. This immediately ingests and analyzes landmark research papers (*Attention Is All You Need*, *LoRA*, *Chain-of-Thought Prompting*) with full citation grounding.

### Step 8: Upload Your Own Papers
Drag and drop your own research PDFs (up to 50 MB) into the **Research Library** dropzone and watch the real pipeline stepper parse, chunk, embed, and synthesize evidence!

---

## API Surface

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health, Ollama availability, active model, DB stats |
| `/api/papers` | GET | List all ingested papers with metadata |
| `/api/papers/upload` | POST | Upload PDF with real multi-stage background pipeline |
| `/api/papers/sample` | POST | 1-click landmark research paper dataset loader |
| `/api/papers/{id}` | GET | Detailed breakdown and citation evidence for paper |
| `/api/papers/{id}/file` | GET | Streams original PDF file for embedded reader |
| `/api/papers/{id}/analyze` | POST | Re-runs structured extraction on paper |
| `/api/recommendations/{id}` | GET | Top-k similar papers with shared concept drivers |
| `/api/graph` | GET | Graph nodes and similarity links for topology view |
| `/api/compare` | POST | Comparative matrix across 2 to 6 papers |
| `/api/compare/export-csv` | GET | Downloads comparison table as CSV |
| `/api/gaps` | GET | Clustered research gaps with confidence & evidence |
| `/api/reports` | POST | Generates Markdown and PDF synthesis reports |
| `/api/settings` | GET/PUT | Manage Ollama endpoint, model, and engine settings |

---

## Running Verification Tests

Run the comprehensive end-to-end test suite:
```bash
python -m tests.test_fastapi
```
All 11 verification steps will run in-process and validate health, PDF parsing, recommendations, graph topology, comparison matrix, CSV export, research gap clustering, and PDF report generation.
