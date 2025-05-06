from fastapi import FastAPI, Request
import pandas as pd
import os
from fastapi.responses import JSONResponse

app = FastAPI()

DATA_FOLDER = "data"  # Folder where all industry CSV files are stored

@app.post("/get-recommendation")
async def get_recommendation(request: Request):
    try:
        input_data = await request.json()
        product = input_data.get("product")
        industry = input_data.get("industry")

        if not product or not industry:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Both 'product' and 'industry' fields are required."}
            )

        # Construct the expected CSV file path
        csv_file_path = os.path.join(DATA_FOLDER, f"{industry}.csv")

        if not os.path.exists(csv_file_path):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"No data file found for industry: {industry}"}
            )

        df = pd.read_csv(csv_file_path)

        # Check for product in the 'Name' column
        if "Name" not in df.columns:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "CSV format invalid. 'Name' column missing."}
            )

        matched_rows = df[df["Name"].str.strip().str.lower() == product.strip().lower()]

        if matched_rows.empty:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Product '{product}' not found in industry '{industry}'."}
            )

        # Convert result to dictionary
        results = matched_rows.to_dict(orient="records")

        return {"status": "success", "recommendations": results}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
