from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import json

app = FastAPI()

# Enable CORS for testing or integration (optional but helpful)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load all CSV files in the data folder
DATA_FOLDER = "data"
dataframes = []

for filename in os.listdir(DATA_FOLDER):
    if filename.endswith(".csv"):
        df = pd.read_csv(os.path.join(DATA_FOLDER, filename))
        dataframes.append(df)

@app.post("/recommend")
async def recommend_products(request: Request):
    try:
        body = await request.json()
        product = body.get("product")
        industry = body.get("industry")

        if not product or not industry:
            return {"error": "Both 'product' and 'industry' fields are required."}

        # Search across all dataframes
        matched_results = []
        for df in dataframes:
            matches = df[
                (df["product"].str.lower() == product.lower()) &
                (df["industry"].str.lower() == industry.lower())
            ]
            if not matches.empty:
                matched_results.extend(matches.to_dict(orient="records"))

        if matched_results:
            return {"status": "success", "recommendations": matched_results}
        else:
            return {"status": "no_matches", "message": "No matching records found."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
