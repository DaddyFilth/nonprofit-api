try:
    from .agent import agent_executor
except ImportError:
    from agent import agent_executor

def run_assistant():
    print("--- Nonprofit API Assistant Started ---")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        # Using the agent_executor imported at the top
        response = agent_executor.invoke({"messages": [("user", user_input)]})
        print(f"AI: {response['messages'][-1].content}\n")

if __name__ == "__main__":
    run_assistant()
