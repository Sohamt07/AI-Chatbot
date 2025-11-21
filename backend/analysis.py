import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import uuid
import json

def perform_eda(df: pd.DataFrame):
    # Build serializable EDA summary
    numeric_df = df.select_dtypes(include=["number"])
    try:
        summary_stats = df.describe(include="all").fillna("").to_dict()
    except Exception:
        summary_stats = {}

    eda = {
        "shape": list(df.shape),
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_stats": summary_stats,
        # correlation only for numeric
        "correlation": numeric_df.corr().round(3).to_dict()
    }
    return eda

def generate_plots(df, out_dir="plots"):
    """
    Save plots into out_dir and return list of absolute file paths.
    Produces:
      - histogram of first numeric column (if exists)
      - correlation heatmap (if >1 numeric column)
    """
    os.makedirs(out_dir, exist_ok=True)
    plot_files = []

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    # HISTOGRAM
    if len(numeric_cols) > 0:
        col = numeric_cols[0]
        filename = f"{uuid.uuid4().hex}_hist_{col}.png"
        path = os.path.join(out_dir, filename)
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True)
        plt.title(f"Histogram of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        plot_files.append(path)

    # HEATMAP
    if len(numeric_cols) > 1:
        filename = f"{uuid.uuid4().hex}_heatmap.png"
        path = os.path.join(out_dir, filename)
        plt.figure(figsize=(8, 6))
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        plot_files.append(path)

    return plot_files
