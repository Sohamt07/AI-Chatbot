# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import pandas as pd
import os
import io
import shutil
from analysis import perform_eda, generate_all_plots, generate_chart
from insights import generate_ai_insights

load_dotenv()

app = FastAPI(title="AI Data Analyst (Gemini)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
PLOTS_ROOT = os.path.join(BASE_DIR, "plots")
os.makedirs(PLOTS_ROOT, exist_ok=True)
app.mount("/plots", StaticFiles(directory=PLOTS_ROOT), name="plots")

# in-memory dataset
df_global = None
dataset_name_global = None

@app.get("/")
def root():
    return {"message": "AI Data Analyst Chatbot Backend Running", "gemini_loaded": bool(os.getenv("GEMINI_API_KEY"))}


def _read_csv_bytes(content_bytes: bytes) -> pd.DataFrame:
    """
    Robust CSV reader: attempts a sequence of strategies to parse messy CSV bytes.
    1) default read_csv on bytes
    2) try latin1 encoding
    3) fallback to python engine and skip bad lines
    Raises the last exception if all attempts fail.
    """
    last_exc = None

    # Try 1: default
    try:
        return pd.read_csv(io.BytesIO(content_bytes))
    except Exception as e:
        last_exc = e

    # Try 2: latin1 encoding
    try:
        return pd.read_csv(io.BytesIO(content_bytes), encoding="latin1")
    except Exception as e:
        last_exc = e

    # Try 3: python engine with skip on bad lines
    try:
        return pd.read_csv(io.BytesIO(content_bytes), engine="python", on_bad_lines="skip")
    except Exception as e:
        last_exc = e

    # If all failed, raise the last exception
    raise last_exc


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file, perform EDA, generate initial plots and AI insights.
    Stores dataset in memory (df_global) for subsequent /ask and /generate_chart calls.
    """
    global df_global, dataset_name_global

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    dataset_name = os.path.splitext(file.filename)[0]
    dataset_name_safe = "".join(c for c in dataset_name if c.isalnum() or c in (" ", "_", "-")).strip()
    dataset_dir = os.path.join(PLOTS_ROOT, dataset_name_safe)

    # fresh folder for this dataset
    if os.path.exists(dataset_dir):
        shutil.rmtree(dataset_dir)
    os.makedirs(dataset_dir, exist_ok=True)

    # read bytes robustly
    contents = await file.read()
    try:
        df = _read_csv_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")

    # store in memory for other endpoints
    df_global = df
    dataset_name_global = dataset_name_safe

    # EDA
    eda = perform_eda(df)

    # initial default plots (frontend can request more specific ones via /generate_chart)
    plot_files = generate_all_plots(df, dataset_dir)
    plot_urls = [f"/plots/{dataset_name_safe}/{os.path.basename(p)}" for p in plot_files]

    # AI insights (Gemini)
    try:
        insights_text = generate_ai_insights(eda)
    except Exception as e:
        insights_text = f"AI insights generation failed: {e}"

    return JSONResponse({
        "message": "CSV uploaded successfully",
        "dataset": dataset_name_safe,
        "eda": eda,
        "insights": insights_text,
        "plots": plot_urls
    })


@app.post("/generate_chart")
async def generate_chart_endpoint(request: Request):
    """
    Expects JSON body:
    {
      "chart_type": "histogram",
      "columns": ["colA", "colB"]
    }
    Requires: a dataset uploaded previously via /upload.
    Returns: { "chart_url": "/plots/<dataset>/<image.png>" }
    """
    global df_global, dataset_name_global
    if df_global is None or dataset_name_global is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded yet. Use /upload first.")

    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON body. Send a JSON object with chart_type and columns.")

    chart_type = payload.get("chart_type")
    columns = payload.get("columns", [])

    if not chart_type:
        raise HTTPException(status_code=400, detail="chart_type is required.")
    if not isinstance(columns, list) or len(columns) == 0:
        raise HTTPException(status_code=400, detail="columns must be a non-empty list of column names.")

    dataset_dir = os.path.join(PLOTS_ROOT, dataset_name_global)
    try:
        saved_path = generate_chart(df_global, chart_type, columns, dataset_dir)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {e}")

    rel_url = f"/plots/{dataset_name_global}/{os.path.basename(saved_path)}"
    return {"chart_url": rel_url}


@app.get("/ask")
async def ask_about_data(query: str):
    """
    Chat-like endpoint: sends a user query plus a small dataset sample to Gemini.
    The Gemini prompt instructs the model to reply in a structured, easy-to-understand format.
    """
    global df_global
    if df_global is None:
        raise HTTPException(status_code=400, detail="No CSV uploaded yet.")

    sample = {
        "columns": sorted(df_global.columns.tolist(), key=lambda x: str(x).lower()),
        "head": df_global.head(10).to_dict(orient="records"),
        "shape": [int(df_global.shape[0]), int(df_global.shape[1])]
    }
    prompt_input = {"query": query, "sample": sample}
    try:
        resp = generate_ai_insights(prompt_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {e}")
    return {"response": resp}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
