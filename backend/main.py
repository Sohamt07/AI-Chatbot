from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import pandas as pd
import os
from analysis import perform_eda, generate_plots
from insights import generate_ai_insights
import uuid

# Load env
load_dotenv()

app = FastAPI(title="AI Data Analyst (Gemini)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure plots directory exists and mount as static
PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)
app.mount("/plots", StaticFiles(directory=PLOTS_DIR), name="plots")

# In-memory store (for demo)
df_global = None


@app.get("/")
def root():
    return {"api_key": os.getenv("GEMINI_API_KEY")}

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    global df_global
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    try:
        # read CSV into pandas
        df_global = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")

    # EDA
    eda = perform_eda(df_global)

    # Plots -> returns relative URLs like /plots/<filename>.png
    plot_files = generate_plots(df_global, out_dir=PLOTS_DIR)

    # Convert plot file paths to URLs the frontend can fetch
    plot_urls = [f"/plots/{os.path.basename(p)}" for p in plot_files]

    # Gemini insights
    insights_text = generate_ai_insights(eda)

    # Return JSON-serializable structure
    return JSONResponse({
        "message": "CSV uploaded successfully",
        "eda": eda,
        "insights": insights_text,
        "plots": plot_urls
    })


@app.get("/ask")
async def ask_about_data(query: str):
    global df_global
    if df_global is None:
        raise HTTPException(status_code=400, detail="No CSV uploaded yet.")
    # Create a compact sample + schema for the model
    sample = {
        "columns": df_global.columns.tolist(),
        "head": df_global.head(10).to_dict(orient="records"),
        "shape": df_global.shape
    }
    prompt_input = {
        "query": query,
        "sample": sample
    }
    resp = generate_ai_insights(prompt_input)
    return {"response": resp}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
