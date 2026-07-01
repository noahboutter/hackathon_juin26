import tool_functions as llmtools
from langchain_ollama import ChatOllama
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOllama(model="llama3.1", temperature=0)

tools = llmtools.TOOLS

system_prompt = """Tu es un expert en ressources humaines et en planification de personnel pour des conducteurs de bus.

Ton rôle est d'aider le planificateur à analyser les fichiers de planning et de services à affecter, en répondant en français, de façon factuelle et chiffrée, en t'appuyant TOUJOURS sur les outils mis à ta disposition plutôt que sur ta mémoire.

Règles importantes :
- N'invente jamais un identifiant d'agent, un numéro de service ou un chiffre : utilise un outil.
- Si une question est ambiguë (ex: pas de date précisée), demande une précision à l'utilisateur 
  plutôt que de deviner.
- Donne des réponses synthétiques et claires, avec les chiffres clés en premier.
"""

prompt = ChatPromptTemplate.from_messages([("system", system_prompt),MessagesPlaceholder(variable_name="chat_history", optional=True),("human", "{input}"),MessagesPlaceholder(variable_name="agent_scratchpad"),])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=8,
)