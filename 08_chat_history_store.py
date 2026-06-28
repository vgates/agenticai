# =====================================================================
# LangChain Chat History - Part 3: Chat History Stores
# =====================================================================
#
# Manually managing Python lists of messages becomes hard to maintain.
# LangChain offers dedicated message history store classes to automatically
# hold, append, and fetch messages.
#
# InMemoryChatMessageHistory is the simplest store—it stores messages in
# local RAM. Other database-backed stores (e.g., Postgres, Redis) follow the
# same interface, allowing you to scale up without changing your code structure.
#
# We will build a Travel Assistant chatbot. The user will discuss their
# vacation plans over several turns. We will use InMemoryChatMessageHistory
# to dynamically track and update the state of the conversation.
# =====================================================================

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
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
    
    # 3. Create the chat history store
    # This object acts as our local in-memory database for messages.
    history_store = InMemoryChatMessageHistory()
    
    # 4. Construct the chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional travel planner. Keep your suggestions highly specific and concise (1-2 sentences)."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_input}")
    ])
    chain = prompt | llm
    
    # 5. Multi-Turn Dialogue Simulation
    # We will run 3 sequential turns, appending inputs/outputs to the store.
    
    # --- TURN 1 ---
    turn_1_input = "Hi! I am planning a 3-day trip to Paris. I love architecture and museum visits."
    print(f"User Turn 1: {turn_1_input}")
    
    # Invoke model with current history (currently empty)
    response_1 = chain.invoke({
        "history": history_store.messages,
        "user_input": turn_1_input
    })
    print(f"AI Response 1: {response_1.content}\n")
    
    # Append both messages to the store to remember them
    # Note: System Messages are kept out of the History Store, because In most AI applications, 
    # the System Message is static instruction—it never changes.
    # Best Practice: Keep the System Message inside the ChatPromptTemplate definition. 
    # This guarantees the system instructions are always at the very top of the prompt.
    # If your bot uses tools to record this entire exchange, you must save the tool messages as well.
    #   LangChain uses the generic add_messages() method to save tool messages.
    # 95% of chat history operations are just saving raw text back-and-forth between a user and an AI
    # hence we use add_user_message(text) and add_ai_message(text)
    history_store.add_user_message(turn_1_input)
    history_store.add_ai_message(response_1.content)
    
    # --- TURN 2 ---
    turn_2_input = "What are the best times of day to visit the Louvre and Eiffel Tower to avoid crowds?"
    print(f"User Turn 2: {turn_2_input}")
    
    # Invoke model with the updated history (now contains 2 messages)
    response_2 = chain.invoke({
        "history": history_store.messages,
        "user_input": turn_2_input
    })
    print(f"AI Response 2: {response_2.content}\n")
    
    # Save Turn 2 to store
    history_store.add_user_message(turn_2_input)
    history_store.add_ai_message(response_2.content)
    
    # --- TURN 3 ---
    turn_3_input = "Great. Can you recommend a boutique hotel near those sites?"
    print(f"User Turn 3: {turn_3_input}")
    
    # Invoke model with the fully updated history (now contains 4 messages)
    response_3 = chain.invoke({
        "history": history_store.messages,
        "user_input": turn_3_input
    })
    print(f"AI Response 3: {response_3.content}\n")
    
    # Save Turn 3 to store
    history_store.add_user_message(turn_3_input)
    history_store.add_ai_message(response_3.content)
    
    # 6. Inspect the final store contents
    print("--- Final Stored Messages in InMemoryChatMessageHistory ---")
    for idx, msg in enumerate(history_store.messages):
        role = msg.__class__.__name__
        print(f"Message #{idx + 1} [{role}]: {msg.content}")
    print("-" * 60)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
