# =====================================================================
# This script demonstrates "Tool Calling" (also known as Function Calling)
# in LangChain using the Google Gemini models (gemini-3.5-flash).
#
# CONCEPT:
# 1. We define a Python function to fetch weather data from an external API
#    (OpenWeatherMap) and wrap it as a LangChain Tool using `@tool`.
#    An LLM is a reasoning engine, not a database. By giving it Tools, we 
#    connect the LLM to the outside world.
# 2. We bind the tool to the ChatGoogleGenerativeAI model.
# 3. When we ask a weather-related query, the LLM determines it needs the
#    tool, pauses execution, and returns a request to call the tool.
# 4. We execute the tool locally with the parameters suggested by the LLM.
# 5. We send the tool output back to the LLM.
# 6. The LLM produces the final response.
# =====================================================================

import os
import requests
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# ---------------------------------------------------------------------
# 1. Initialize Configuration and Load Environment Variables
# ---------------------------------------------------------------------
# Load environment variables from the .env file
load_dotenv()

# Verify that the Gemini API Key is present
if not os.environ.get("GOOGLE_API_KEY"):
    print("[WARNING] GOOGLE_API_KEY not found in environment. Please add it to your .env file.")

# ---------------------------------------------------------------------
# 2. Helper function to generate mock weather data
# ---------------------------------------------------------------------
def get_mock_weather(location: str) -> str:
    """
    Returns mock weather data if no OpenWeatherMap API key is provided.
    """
    mock_db = {
        "london": "Weather in London, GB: 15.5°C, Light rain, Humidity: 82%",
        "new york": "Weather in New York, US: 22.0°C, Clear sky, Humidity: 45%",
        "tokyo": "Weather in Tokyo, JP: 19.8°C, Few clouds, Humidity: 60%",
        "delhi": "Weather in Delhi, IN: 38.5°C, Haze, Humidity: 30%",
        "new delhi": "Weather in New Delhi, IN: 38.5°C, Haze, Humidity: 30%",
        "paris": "Weather in Paris, FR: 17.2°C, Scattered clouds, Humidity: 55%",
        "sydney": "Weather in Sydney, AU: 14.0°C, Clear sky, Humidity: 70%",
    }
    
    # Normalize search query
    loc_clean = location.lower().strip()
    
    # Look for exact or partial matches in the mock database
    for city, weather_info in mock_db.items():
        if city in loc_clean:
            return f"[MOCK WEATHER DATA] {weather_info}"
            
    # Deterministic fallback based on character codes if city is not in mock_db
    temps = [12, 18, 25, 30, 8]
    descs = ["Partly cloudy", "Overcast", "Sunny", "Light shower", "Clear sky"]
    humidities = [50, 65, 40, 80, 55]
    idx = sum(ord(c) for c in loc_clean) % len(temps)
    
    return f"[MOCK WEATHER DATA] Weather in {location.title()}: {temps[idx]}°C, {descs[idx]}, Humidity: {humidities[idx]}%"


# ---------------------------------------------------------------------
# 3. Define the Weather Tool using LangChain's @tool decorator
# ---------------------------------------------------------------------
# The docstring of this function is extremely important! 
# LangChain extracts the docstring and function signature to describe the tool 
# to the LLM, so the LLM knows *when* and *how* to use it.
# Your docstrings are the actual instructions for the AI.
@tool
def get_weather(location: str) -> str:
    """
    Fetch the current weather details for a given location/city name.
    
    Args:
        location: The name of the city/location to check weather for (e.g. 'London', 'Tokyo').
        
    Returns:
        A string describing the temperature, weather conditions, and humidity.
    """
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    
    # If the user has not configured the OpenWeatherMap API key, fallback to mock data
    if not api_key:
        print(f" -> [Tool Log] 'get_weather' invoked for '{location}'. (Using mock fallback; set OPENWEATHERMAP_API_KEY in .env for real API calls)")
        return get_mock_weather(location)
    
    print(f" -> [Tool Log] 'get_weather' invoked for '{location}'. Querying OpenWeatherMap API...")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"  # Retrieve temperature in Celsius
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"]
            city_name = data["name"]
            country = data["sys"]["country"]
            return f"Weather in {city_name}, {country}: {temp}°C, {desc.capitalize()}, Humidity: {humidity}%"
        elif response.status_code == 401:
            print(" -> [Tool Log] API Error: Unauthorized (401). Falling back to mock data.")
            return f"Error: Invalid OpenWeatherMap API Key. Fallback data: {get_mock_weather(location)}"
        elif response.status_code == 404:
            return f"Error: Location '{location}' not found by OpenWeatherMap API."
        else:
            return f"Error: Weather API returned status code {response.status_code}."
            
    except Exception as e:
        print(f" -> [Tool Log] Network Error: {str(e)}. Falling back to mock data.")
        return f"Error connecting to Weather API: {str(e)}. Fallback data: {get_mock_weather(location)}"


# ---------------------------------------------------------------------
# 4. Agent Tool Calling Runner (The Step-by-Step Concept)
# ---------------------------------------------------------------------
def run_agentic_weather_check(user_query: str):
    """
    Executes a tool-calling conversation flow.
    Demonstrates how the LLM determines tool usage, returns a tool call payload,
    and receives the tool execution output to generate a final answer.
    """
    print("=" * 80)
    print(f"User Query: '{user_query}'")
    print("=" * 80)
    
    # 1. Initialize the LLM 
    # Temperature: Controls the flatness of the probability distribution for the next token. 
    # Higher temperature makes the output more creative/random; 0.0 makes it deterministic 
    # We set temperature=0 for deterministic behavior when using tools.
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    
    # 2. Bind the tools to the LLM
    # This informs the Gemini model about the tool's schema (name, description, args)
    # and allows Gemini to return tool call blocks in its response.
    llm_with_tools = llm.bind_tools([get_weather])
    
    # 3. Create the list of messages with the user query
    # In LangChain, chat models do not accept plain text strings directly. Instead, they 
    #   expect a list of Message Objects that represent the conversation history.
    # The Message Types in LangChain:
    #   1. HumanMessage: A message sent by the user (What is the weather in Tokyo?)
    #   2. AIMessage: A response generated by the AI model. (AI decides to call a tool, or gives a final reply.)
    #   3. SystemMessage: Developer instructions to set the AI's behavior/persona. 
    #                     (You are a helpful assistant who must speak in French)
    #   4. ToolMessage: The output returned after executing a tool function.("19.8°C, Few clouds")
    # By storing these messages in a list, we can track the conversation state step-by-step.
    messages = [HumanMessage(content=user_query)]
    
    print("\n[Step 1] Sending prompt to LLM (with weather tool bound)...")
    # First model invocation
    first_response = llm_with_tools.invoke(messages)
    
    # Append the model's response to the conversation history
    messages.append(first_response)
    
    # 4. Check if the LLM requested a tool call
    if first_response.tool_calls:
        print("\n[Step 2] LLM detected tool usage is required!")
        # Modern models are trained to look for independent entities in a single query
        # When you ask: "What is the weather in Pune right now? Compare it with Thrissur.", 
        #   the model's semantic parser splits your query into two distinct requirements:
        #   1. Needs weather for Pune.
        #   2. Needs weather for Thrissur.
        # we use a loop to execute both calls at the same time
        # Both outputs are wrapped in separate ToolMessage objects and sent back to the LLM together.
        # This is an example of Parallel Tool Calling (The Pune & Thrissur Example)
        # We also have Sequential Reasoning (The Chain Reaction)
        #   Sometimes, the LLM cannot know it needs a second tool call until it gets the result 
        #   of the first one. This is called the ReAct (Reasoning + Acting) loop.  
        #   For example, if you ask: "Who is the current prime minister of India, and what is the 
        #   weather in their birth city?" The LLM cannot call the weather tool immediately because it 
        #   doesn't know the birth city yet.
        # The LLM decides the number of calls by:
        #   - Analyzing independence: If it can query both at once, it requests them 
        #       in parallel (like Pune and Thrissur).
        #   - Analyzing dependency: If it needs information from Step A to do Step B, it requests them 
        #       one-by-one in a continuous loop until it has enough data to formulate the final answer.
        for tool_call in first_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            print(f"   - Tool Selected: '{tool_name}'")
            print(f"   - Arguments Extracted: {tool_args}")
            print(f"   - Tool Call ID: {tool_id}")
            
            # Execute the tool if it matches 'get_weather'
            if tool_name == "get_weather":
                # We can call the tool directly using the .invoke method from LangChain
                tool_output = get_weather.invoke(tool_args)
                print(f"   - Tool Output Obtained: {tool_output}")
                
                # Create a ToolMessage to pass the result back to the model.
                # The tool_call_id MUST match the id generated by the LLM call.
                tool_message = ToolMessage(content=str(tool_output), tool_call_id=tool_id)
                messages.append(tool_message)
            else:
                print(f"   - Warning: LLM requested unknown tool: '{tool_name}'")
        
        # 5. Send the conversation history (including the tool response) back to the LLM
        print("\n[Step 3] Sending tool execution output back to LLM...")
        final_response = llm_with_tools.invoke(messages)
        
        print("\n[Final Response from LLM]:")
        print(final_response.content)
        
    else:
        print("\n[Step 2] LLM decided no tool was needed for this request.")
        print("\n[Final Response from LLM]:")
        print(first_response.content)
        
    print("\n" + "=" * 80 + "\n")


# ---------------------------------------------------------------------
# 5. Execution Main Block
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Test Case 1: Query that triggers the Weather Tool
    # This should trigger the LLM to call the 'get_weather' tool.
    query_with_tool = "What is the weather in Pune right now? Compare it with Thrissur."
    run_agentic_weather_check(query_with_tool)
    
    # Test Case 2: Query that does NOT trigger any tools
    # This should be answered directly by the LLM without calling 'get_weather'.
    query_without_tool = "What is the difference between tool calling and standard LLM chat?"
    run_agentic_weather_check(query_without_tool)

# ---------------------------------------------------------------------
# Note:
# LLM does not execute your code. LLM only generates the intent to call 
# a tool. It looks at the blueprint, stops generating chat text, and 
# outputs a JSON instructions block saying:"Please run the function 
# named get_weather with the parameter location="Tokyo". 
# 
# Python script receives this JSON block, parses it, physically executes 
# the Python function get_weather("Tokyo"), and grabs the return value.
# 
# If the LLM could actually execute code on your machine, a malicious 
# user could trick it (via prompt injection) into running commands like: 
# os.system("rm -rf /") or deleting all files. Because your Python script 
# is the one in control of execution, you decide what the LLM is allowed 
# to do. 
# The LLM doesn't need to know your database passwords or have access to 
# your local files. Your local Python script connects to your database, 
# retrieves the data, and only hands the final, safe text result to the LLM.
# ---------------------------------------------------------------------
