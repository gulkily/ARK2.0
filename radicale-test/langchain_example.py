"""
Example usage of CalendarToolAdapter with LangChain

This script demonstrates how to:
1. Initialize the CalendarToolAdapter
2. Create a LangChain agent with calendar tools
3. Perform basic calendar operations
4. Handle errors and responses
"""

import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import Tool
from langchain_tool_adapter import CalendarToolAdapter

# Load environment variables from .env file
load_dotenv()

# Initialize the calendar tool adapter with credentials from .env
calendar_adapter = CalendarToolAdapter(
    url=os.getenv("RADICALE_URL"),
    username=os.getenv("RADICALE_USERNAME"),
    password=os.getenv("RADICALE_PASSWORD")
)

# Get all calendar tools
tools = calendar_adapter.get_all_tools()

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=(
        "You are a helpful calendar assistant. "
        "You can help users manage their calendar events. "
        "Always confirm the action before executing it. "
        "If you're unsure about any parameters, ask for clarification."
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Initialize the LLM with API key from .env
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # or any other supported model
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create the agent
agent = create_openai_functions_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

def run_calendar_operation(operation: str) -> str:
    """
    Run a calendar operation using the agent
    
    Args:
        operation: The operation to perform (e.g., "List my events for today")
    
    Returns:
        The result of the operation
    """
    try:
        # Initialize empty chat history for each operation
        chat_history = []
        result = agent_executor.invoke({
            "input": operation,
            "chat_history": chat_history
        })
        return result["output"]
    except Exception as e:
        return f"Error performing operation: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Example 1: List all calendars
    print("\nExample 1: Listing all calendars")
    print(run_calendar_operation("What calendars do I have access to?"))
    
    # Example 2: Add an event
    print("\nExample 2: Adding an event")
    print(run_calendar_operation(
        "Add a meeting with John tomorrow at 2pm for 1 hour in my work calendar"
    ))
    
    # Example 3: List events
    print("\nExample 3: Listing events")
    print(run_calendar_operation(
        "Show me all events in my work calendar for tomorrow"
    ))
    
    # Example 4: Update an event
    print("\nExample 4: Updating an event")
    print(run_calendar_operation(
        "Change the meeting with John to 3pm tomorrow"
    ))
    
    # Example 5: Delete an event
    print("\nExample 5: Deleting an event")
    print(run_calendar_operation(
        "Cancel the meeting with John tomorrow"
    ))

# Notes:
# 1. OpenAI API key is read from the .env file:
#    OPENAI_API_KEY=your-api-key
#
# 2. Create a .env file with your Radicale credentials:
#    RADICALE_URL=http://localhost:5232
#    RADICALE_USERNAME=your-username
#    RADICALE_PASSWORD=your-password
#
# 3. The agent will handle date parsing and formatting automatically
#
# 4. Error handling is included in the run_calendar_operation function
#
# 5. The agent will ask for clarification if any parameters are missing or unclear 