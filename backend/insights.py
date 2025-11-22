import os
from dotenv import load_dotenv
from google import genai
import json

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Please create a .env file.")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


# ---------------------------------------------------
# Helper: Convert EDA dict → readable text
# ---------------------------------------------------
def _eda_to_text(eda):
    text = []
    text.append(f"Shape: {eda.get('shape')}")
    text.append(f"Columns: {', '.join(eda.get('columns', []))}")

    # missing values (top 10)
    mv = eda.get("missing_values", {})
    if mv:
        mv_sorted = sorted(mv.items(), key=lambda x: x[1], reverse=True)[:10]
        text.append("Missing values (top): " +
                    ", ".join([f"{k}:{v}" for k, v in mv_sorted]))

    # correlation matrix info
    corr = eda.get("correlation", {})
    if isinstance(corr, dict) and corr:
        text.append("Correlation matrix detected (trimmed).")

    return "\n".join(text)


# ---------------------------------------------------
# Main: Generate insights using Gemini
# ---------------------------------------------------
def generate_ai_insights(eda_data):
    """
    eda_data may be:
      • The EDA dict from perform_eda()
      • A dict with {'query': '...', 'sample': {...}} for Q&A
    """

    # Case 1: User is asking a question
    if isinstance(eda_data, dict) and "query" in eda_data:
        user_query = eda_data["query"]
        sample = eda_data.get("sample", {})

        prompt = f"""
You are an expert data analyst. The user asked: "{user_query}"

Here is a small sample of the dataset:
{json.dumps(sample, indent=2)}

Provide:
- A clear answer
- Insights based on available sample
- Steps to compute deeper insights
- Short code snippets if useful
Keep it concise.
"""
    else:
        # Case 2: Full dataset EDA summary
        eda_text = _eda_to_text(eda_data)

        prompt = f"""
You are an expert data analyst. When I give you an EDA summary, respond in a first-person chatbot voice. Provide the following:

• Top 5 important insights
• Any correlations or trends
• Possible anomalies
• Recommended next steps for deeper analysis

Keep the response concise, limited to 8–12 sentences, and avoid emojis or any statements about interpreting the query.

EDA SUMMARY:
{eda_text}
"""

    # ---------------------------------------------------
    # Generate using new Gemini 2.0 API
    # ---------------------------------------------------
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text
