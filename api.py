from fastapi import FastAPI, Request
import boto3
import os
import pandas as pd
from botocore.exceptions import NoCredentialsError
import io

# Initialize FastAPI
app = FastAPI()

# Set up AWS credentials from environment variables (Render environment)
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
bucket_name = os.getenv("AWS_S3_BUCKET_NAME")

# Set up S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# Root endpoint for health check
@app.get("/")
async def root():
    return {"message": "API is up and running!"}

@app.post("/upload-product-data")
async def receive_data(request: Request):
    try:
        # Receive JSON data from the client
        data = await request.json()

        # Check if 'products' data is present
        products = data.get("products")
        if not products:
            return {"status": "error", "message": "No 'products' field found"}

        # Convert products list to a DataFrame
        df = pd.DataFrame(products)

        # Save to AWS S3 as a CSV file
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)  # Move cursor to the beginning of the buffer

        s3_client.put_object(
            Bucket=bucket_name,
            Key="uploaded_from_salesforce.csv",  # Specify the key in S3
            Body=csv_buffer.getvalue()  # Get CSV content as string
        )

        return {"status": "success", "message": "Data successfully uploaded to AWS S3"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

