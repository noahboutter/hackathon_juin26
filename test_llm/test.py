from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def calc_sum (a: int, b:int) -> int:
    """
    Returns the result of the sum of two integers a and b
    """
    return 3.
    


agent = create_agent(
    model="ollama:llama3.1:latest",
    tools=[get_weather,calc_sum],
    system_prompt="You are a helpful assistant. Use only the tools that are given in order to generate your responses. Do not do your own calculations",
    #debug=True
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Quelle est la somme de l'entier 2 et de l'entier 4 ?"}]}
)

print(result["messages"][-1].content_blocks)