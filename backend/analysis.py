# analysis.py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import uuid
import numpy as np

# Helper to convert numpy types to Python scalars for JSON-serializable outputs
def _to_py(v):
    try:
        if isinstance(v, (np.integer, np.floating)):
            return v.item()
        if pd.isna(v):
            return None
        return v
    except Exception:
        return v

def perform_eda(df: pd.DataFrame):
    numeric_df = df.select_dtypes(include=["number"])

    # summary
    try:
        summary_stats = df.describe(include="all").replace([np.nan, np.inf, -np.inf], None).to_dict()
    except Exception:
        summary_stats = {}

    # dtypes dictionary
    dtypes = {k: str(v) for k, v in df.dtypes.to_dict().items()}

    # missing values (convert NaN → None)
    missing_vals = df.isnull().sum().replace([np.nan], None).to_dict()

    # correlation (convert NaN → None)
    corr = (
        numeric_df.corr()
        .replace([np.nan, np.inf, -np.inf], None)
        .to_dict()
    )

    eda = {
    "shape": list(df.shape),

    # Sorted alphabetically
    "columns": sorted(df.columns.tolist()),

    "dtypes": dict(sorted(dtypes.items(), key=lambda x: x[0])),

    "missing_values": dict(sorted(missing_vals.items(), key=lambda x: x[0])),

    # correlation sorted by column name
    "correlation": {
        col: dict(sorted(vals.items(), key=lambda x: x[0]))
        for col, vals in sorted(corr.items(), key=lambda x: x[0])
    },

    "summary_stats": summary_stats
}


    return eda


# Chart generation functions
# NOTE: These functions create files and return their absolute paths.
def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def _unique_filename(prefix, suffix="png"):
    return f"{uuid.uuid4().hex}_{prefix}.{suffix}"

def generate_all_plots(df, save_dir):
    """
    Generate a broad set of visualizations and save them in save_dir.
    Returns list of saved file paths (relative or absolute depending on how you use it).
    The frontend should call /generate_chart for specific charts on demand, but this function
    is useful to create an initial set of default visuals.
    """
    _ensure_dir(save_dir)
    files = []

    # Numeric columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # HISTOGRAMS (one per numeric column, up to 6 to avoid too many files)
    for col in numeric_cols[:6]:
        fname = _unique_filename(f"hist_{col}")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(6, 4))
        sns.histplot(df[col].dropna(), kde=True)
        plt.title(f"Histogram of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # KDE (first numeric column)
    if len(numeric_cols) >= 1:
        col = numeric_cols[0]
        fname = _unique_filename(f"kde_{col}")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(6, 4))
        sns.kdeplot(df[col].dropna(), fill=True)
        plt.title(f"KDE of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # BOXPLOT (for each numeric col up to 4)
    for col in numeric_cols[:4]:
        fname = _unique_filename(f"box_{col}")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(6, 4))
        sns.boxplot(x=df[col].dropna())
        plt.title(f"Boxplot of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # VIOLIN (first numeric col)
    if len(numeric_cols) >= 1:
        col = numeric_cols[0]
        fname = _unique_filename(f"violin_{col}")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(6, 4))
        sns.violinplot(x=df[col].dropna())
        plt.title(f"Violin plot of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # COUNTPLOTS (categorical columns up to 3)
    for col in cat_cols[:3]:
        fname = _unique_filename(f"count_{col}")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(8, 5))
        order = df[col].value_counts().index[:20]
        sns.countplot(y=col, data=df, order=order)
        plt.title(f"Countplot of {col}")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # PIE (if small unique categories)
    for col in cat_cols[:2]:
        vc = df[col].value_counts()
        if 1 < len(vc) <= 8:
            fname = _unique_filename(f"pie_{col}")
            path = os.path.join(save_dir, fname)
            plt.figure(figsize=(6, 6))
            vc.plot.pie(autopct="%1.1f%%")
            plt.ylabel("")
            plt.title(f"Pie chart of {col}")
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
            files.append(path)

    # CORRELATION HEATMAP (if more than 1 numeric column)
    if len(numeric_cols) > 1:
        fname = _unique_filename("heatmap")
        path = os.path.join(save_dir, fname)
        plt.figure(figsize=(8, 6))
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation heatmap")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        files.append(path)

    # PAIRPLOT (only if <= 6 numeric columns and dataset smallish)
    try:
        if 2 <= len(numeric_cols) <= 6 and df.shape[0] <= 5000:
            fname = _unique_filename("pairplot")
            path = os.path.join(save_dir, fname)
            sns.pairplot(df[numeric_cols].dropna().sample(min(500, df.shape[0])))
            plt.savefig(path)
            plt.close()
            files.append(path)
    except Exception:
        # ignore pairplot errors (heavy)
        pass

    return files


# A dynamic chart generator for the new /generate_chart endpoint
# chart_type: string, columns: list of column names, df: dataframe, out_dir: folder to save
def generate_chart(df, chart_type, columns, out_dir):
    """
    Supported chart_type values:
    histogram, kde, box, violin, scatter, line, bar, countplot, pie, pairplot, heatmap, regplot
    columns: list of column names (length validated per chart)
    """
    _ensure_dir(out_dir)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    # Chart requirements dictionary (min/max or 'any'/'multiple')
    CHART_REQ = {
        "histogram": {"min": 1, "max": 1},
        "kde": {"min": 1, "max": 1},
        "box": {"min": 1, "max": 1},
        "violin": {"min": 1, "max": 1},
        "scatter": {"min": 2, "max": 2},
        "line": {"min": 2, "max": 2},
        "bar": {"min": 2, "max": 2},
        "countplot": {"min": 1, "max": 1},
        "pie": {"min": 1, "max": 1},
        "pairplot": {"min": 2, "max": None},
        "heatmap": {"min": 2, "max": None},
        "regplot": {"min": 2, "max": 2}
    }

    if chart_type not in CHART_REQ:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    req = CHART_REQ[chart_type]
    if req["max"] is None:
        ok = len(columns) >= req["min"]
    else:
        ok = req["min"] <= len(columns) <= req["max"]
    if not ok:
        max_msg = "or more" if req["max"] is None else f"up to {req['max']}"
        raise ValueError(f"Chart '{chart_type}' requires between {req['min']} and {req.get('max', 'n')} columns. You provided {len(columns)}.")

    # sanitize columns
    for c in columns:
        if c not in df.columns:
            raise ValueError(f"Column '{c}' not found in dataset.")

    # Build filename
    safe_cols = "_".join([str(c).replace(" ", "_") for c in columns])
    fname = _unique_filename(f"{chart_type}_{safe_cols}")
    path = os.path.join(out_dir, fname)

    # Generate charts
    plt.figure(figsize=(8, 5))
    if chart_type == "histogram":
        col = columns[0]
        sns.histplot(df[col].dropna(), kde=True)
        plt.title(f"Histogram of {col}")

    elif chart_type == "kde":
        col = columns[0]
        sns.kdeplot(df[col].dropna(), fill=True)
        plt.title(f"KDE of {col}")

    elif chart_type == "box":
        col = columns[0]
        sns.boxplot(x=df[col].dropna())
        plt.title(f"Boxplot of {col}")

    elif chart_type == "violin":
        col = columns[0]
        sns.violinplot(x=df[col].dropna())
        plt.title(f"Violin plot of {col}")

    elif chart_type == "countplot":
        col = columns[0]
        order = df[col].value_counts().index[:30]
        sns.countplot(y=col, data=df, order=order)
        plt.title(f"Countplot of {col}")

    elif chart_type == "pie":
        col = columns[0]
        vc = df[col].value_counts()
        vc.plot.pie(autopct="%1.1f%%")
        plt.ylabel("")
        plt.title(f"Pie chart of {col}")

    elif chart_type == "scatter":
        x, y = columns[0], columns[1]
        sns.scatterplot(x=df[x], y=df[y])
        plt.title(f"Scatter: {y} vs {x}")

    elif chart_type == "line":
        x, y = columns[0], columns[1]
        plt.plot(df[x], df[y])
        plt.title(f"Line: {y} vs {x}")

    elif chart_type == "bar":
        x, y = columns[0], columns[1]
        # If y is numeric, plot aggregated mean; else count
        if pd.api.types.is_numeric_dtype(df[y]):
            agg = df.groupby(x)[y].mean().sort_values(ascending=False)[:30]
            agg.plot.bar()
            plt.title(f"Bar: mean({y}) by {x}")
        else:
            vc = df.groupby(x)[y].count().sort_values(ascending=False)[:30]
            vc.plot.bar()
            plt.title(f"Bar: counts of {y} by {x}")

    elif chart_type == "regplot":
        x, y = columns[0], columns[1]
        sns.regplot(x=df[x], y=df[y], scatter_kws={"s": 10}, line_kws={"color": "red"})
        plt.title(f"Regression plot: {y} vs {x}")

    elif chart_type == "pairplot":
        sel = df[columns].dropna()
        # sample if too large
        if sel.shape[0] > 1000:
            sel = sel.sample(1000)
        pair = sns.pairplot(sel)
        pair.fig.suptitle("Pairplot", y=1.02)
        pair.savefig(path)
        plt.close()
        return path  # already saved via pairplot

    elif chart_type == "heatmap":
        sel = df[columns].select_dtypes(include=["number"]).dropna()
        if sel.shape[1] < 2:
            raise ValueError("Heatmap requires at least 2 numeric columns.")
        sns.heatmap(sel.corr(), annot=True, cmap="coolwarm")
        plt.title("Heatmap (correlation)")

    else:
        plt.close()
        raise ValueError(f"Chart type not implemented: {chart_type}")

    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path
