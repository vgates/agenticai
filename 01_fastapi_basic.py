# Imports the FastAPI class from the fastapi library. 
# This class provides all the core functionality needed to build your API, 
#   handle web requests, and automatically generate documentation.
from fastapi import FastAPI

# Create an instance of the FastAPI class and store it in a variable named app.
# This app object is the main point of interaction for your entire API.
# It is what the web server (like Uvicorn) talks to when directing web traffic 
#   to your Python code.
app = FastAPI()

# Python decorator. When a user visits the root URL using a GET request, 
#   run the function right below this. @app: Refers to the FastAPI instance created above
# .get: Refers to the HTTP GET method
# "/": is the URL path
@app.get("/")

# defines the Python function that will trigger when someone hits the root URL
# async def: This tells Python that this is an asynchronous function. 
# FastAPI is built on modern asynchronous architecture, meaning it can handle thousands 
#   of concurrent requests efficiently without blocking your server while waiting for 
#   slow operations (like database queries).
async def root():
    return {"message":"Hello Agentic-AI. I am live."}


# to Run the application using the Uvicorn Command
#   uvicorn <file-name>:<variable-name-flask-instance> --reload
#   uvicorn 01_fastapi_basic:app --reload
#   --reload: tells Uvicorn to automatically restart the server whenever you make changes in the code
# to Stop: Ctrl  + C