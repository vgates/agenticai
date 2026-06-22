from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from the .env file
# Create a .env file and GOOGLE_API_KEY=<api-key-from-aistudio-google-com>
load_dotenv()

# Initialize the Gemini model 
# (It automatically picks up GOOGLE_API_KEY from the environment)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")

# Invoke and print response
response = llm.invoke("What do you think about agentic ai?")
print(response.content)
