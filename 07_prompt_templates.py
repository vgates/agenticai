# =====================================================================
# LangChain Chat History - Part 2: Prompt Templates & Placeholders
# =====================================================================
#
# Building lists of message objects manually is tedious. Instead, we use
# ChatPromptTemplate and MessagesPlaceholder.
#
# MessagesPlaceholder tells LangChain to dynamically inject a list of
# message objects (the chat history) into a specific spot in our template.
#
# We will create an encouraging Math Tutor bot. The system prompt instructs
# the tutor to explain things step-by-step. The template takes:
# 1. A static system message.
# 2. A list of prior messages ('history').
# 3. The new human query ('user_input').
# =====================================================================

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI


def main():
    # 1. Load environment variables
    load_dotenv()
    
    if not os.environ.get("GOOGLE_API_KEY"):
        print("[ERROR] GOOGLE_API_KEY not found in environment. Please add it to your .env file.")
        return
        
    # 2. Initialize Gemini (gemini-3.5-flash)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    print("Gemini model initialized successfully.\n")
    
    # 3. Create the ChatPromptTemplate
    # The variable name "history" represents the list of prior messages.
    # The variable name "user_input" represents the new question.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an encouraging math tutor. Always explain things step-by-step with clear logic."),
        MessagesPlaceholder(variable_name="history"),  # Dynamically injects messages here
        ("human", "{user_input}")                       # Inject the user's latest question here
    ])
    
    print("--- Prompt Template Structure ---")
    for i, step in enumerate(prompt.messages):
        print(f"Step {i+1}: {step}")
    print("-" * 40 + "\n")
    
    # 4. Construct the LangChain Expression Language (LCEL) chain
    # The pipe '|' connects the prompt output to the model input.
    # In LangChain, | is used to connect different components together, 
    #   like an assembly line.This style of coding is called LCEL.
    #   When you call chain.invoke(), LangChain automatically feeds your 
    #   dictionary into prompt, takes the output of prompt, and feeds it 
    #   directly into llm.
    chain = prompt | llm
    
    # 5. Simulate our conversation history
    # This list represents the historical conversation so far.
    history = [
        HumanMessage(content="Can you explain what a derivative is in calculus?"),
        AIMessage(content="Sure! In calculus, a derivative measures how a function changes as its input changes. Think of it as the instantaneous rate of change or the slope of the curve at a specific point.")
    ]
    
    # The user's new question
    user_input = "Great. What is the derivative of x squared, and why?"
    
    print(f"Simulating user query: '{user_input}'")
    print(f"Passing {len(history)} messages in 'history' placeholder.")
    
    # 6. Invoke the chain
    # We pass the dictionary containing values for both placeholders.
    response = chain.invoke({
        "history": history,
        "user_input": user_input
    })
    
    print(f"\n[AI Response]:\n{response.content}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()


# MessagesPlaceholder lets you separate your template definition from 
# the conversational history stream. LangChain handles the merging automatically.