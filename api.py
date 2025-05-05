from fastapi import FastAPI, Request
import pandas as pd
import openai
import os
import uvicorn

# Initialize FastAPI
app = FastAPI()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set in Render environment settings

# Load base and industry data (assumes CSVs are in the same folder as this script)
base_df = pd.read_csv("../recommendation-engine/Base.csv")
industry_files = {
    "Apparel": "../recommendation-engine/Apparel.csv",
    "Construction": "../recommendation-engine/Construction.csv",
    "Energy": "../recommendation-engine/Energy.csv",
    "Hospitality": "../recommendation-engine/Hospitality.csv",
    "Transportation": "../recommendation-engine/Transportation.csv"
}
industry_dfs = {k: pd.read_csv(v) for k, v in industry_files.items()}

# Util: Get recommendation
def get_recommendation(product_name, industry):
    base_product = base_df[base_df["Base Name"] == product_name]
    if base_product.empty:
        return None

    base_code = base_product["Base Code"].values[0]
    base_moq = base_product["Minimum Order Quantity"].values[0]
    base_terms = base_product["Payment Terms"].values[0]

    reco_product = product_name
    reco_code = base_code
    moq = base_moq
    terms = base_terms

    if industry in industry_dfs:
        df = industry_dfs[industry]
        match = df[df[df.columns[0]].str.startswith(product_name)]
        if not match.empty:
            reco_product = match[match.columns[0]].values[0]
            reco_code = match[match.columns[1]].values[0]
            moq = match["Minimum Order Quantity"].values[0]
            terms = match["Payment Terms"].values[0]

    return {
        "Product": product_name,
        "Industry": industry,
        "Recommended Product": reco_product,
        "Recommended Code": reco_code,
        "MOQ": int(moq),
        "Payment Terms": terms
    }

# Util: Get insights from GPT
def get_deal_insights(product, industry, moq, payment_terms):
    prompt = f"""
    Product: {product}
    Industry: {industry}
    Recommended Product: {product}-{industry[0].upper()}
    Minimum Order Quantity: {moq}
    Payment Terms: {payment_terms}

    Based on this context, answer the following:

    1. What is the probability (0-100%) of closing this deal?
    2. What is the profitability rating? (Low / Medium / High)
    3. What should be the next best step for the sales rep to close this deal?

    Format the response as:
    Deal Probability: <percent>
    Profitability: <rating>
    Next Step: <action>
    """
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# API route
@app.post("/upload-product-data")
async def receive_data(request: Request):
    try:
        data = await request.json()
        products = data.get("products")

        if not products:
            return {"status": "error", "message": "No 'products' field found"}

        df = pd.DataFrame(products)
        # Save to project root
        df.to_csv("../uploaded_from_salesforce.csv", index=False)

        # For demo: use first product and a default industry
        first_product = df.iloc[0]
        product_name = first_product["Base Name"]
        industry = data.get("industry", "Apparel")  # Allow industry
