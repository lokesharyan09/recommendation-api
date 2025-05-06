from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
import os

app = FastAPI()

# Path where your CSV files are stored (adjust if you're using a different path)
CSV_FOLDER = "data"

# Load all CSV files into a single DataFrame at startup
all_dataframes = []

for filename in os.listdir(CSV_FOLDER):
    if filename.endswith(".csv"):
        df = pd.read_csv(os.path.join(CSV_FOLDER, filename))
        all_dataframes.append(df)

combined_df = pd.concat(all_dataframes, ignore_index=True)

@app.get("/")
def health_check():
    return {"message": "API is up and running!"}

@app.post("/get-recommendations")
async def get_recommendations(request: Request):
    try:
        body = await request.json()
        product = body.get("product")
        industry = body.get("industry")

        if not product or not industry:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing 'product' or 'industry' field"}
            )

        # Filter the DataFrame based on product and industry
        filtered_df = combined_df[
            (combined_df["product"].str.lower() == product.lower()) &
            (combined_df["industry"].str.lower() == industry.lower())
        ]

        if filtered_df.empty:
            return {"status": "success", "recommendations": []}

        # Format results as list of dictionaries
        recommendations = filtered_df.to_dict(orient="records")

        return {"status": "success", "recommendations": recommendations}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
