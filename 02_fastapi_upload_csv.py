# pandas is imported to handle the data manipulation
import pandas as pd
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# decorator that defines a POST route
@app.post("/upload/csv")
# file: UploadFile = File(...): This tells FastAPI to expect a file upload in 
#   the request body. Using UploadFile is great because it streams large files 
#   and stores them in memory (or a temporary file on disk if they get too big), 
#   preventing your server from running out of RAM.
async def upload_csv(file: UploadFile = File(...)): 
    # file.file: This accesses the actual Python file-like object (a SpooledTemporaryFile) 
    #   wrapping the uploaded data.
    #   First file: name of the variable you defined in your function argument. An instance 
    #       of FastAPI's UploadFile class. It contains metadata about the upload, such as 
    #       file.filename (the name of the file) and file.headers (the content type).
    #   second .file: an attribute inside that wrapper. It exposes the actual, raw Python 
    #       file-like object (specifically a SpooledTemporaryFile).
    # pd.read_csv(...): Pandas can read directly from file streams. It parses the CSV data 
    #   immediately into a Pandas DataFrame (df) without needing to save the file to your 
    #   hard drive first. Pandas pd.read_csv() function doesn't know how to read a 
    #   FastAPI UploadFile object directly, but it does know how to read a standard Python 
    #   file stream. By passing file.file, you are reaching inside FastAPI's wrapper, 
    #   grabbing the raw file stream, and handing it directly to Pandas to parse.
    df = pd.read_csv(file.file)
    return {"rows": len(df), "data": df.to_dict(orient="records")}


# To run the application:
#   uvicorn 02_fastapi_upload_csv:app --reload
# Before you run make sure that you have installed python-multipart
#   uv add python-multipart

# How to Test a FastAPI File Upload in Postman
#   - Set the HTTP Method to POST: API code uses @app.post, so select POST from the dropdown menu.
#   - Enter the Correct URL: http://127.0.0.1:8000/upload/csv.
#   - Select the "Body" Tab and Choose "form-data": Since we are doing multipart upload, request body must be sent as form-data.
#   - Configure the Key-Value Pair:
#   - Key Name: "file". as it is the exact variable name in the function argument (file: UploadFile).
#   - Key Type: Select "Text" to "File". 
#   - Value: Attached your CSV file
#   - Hit Send