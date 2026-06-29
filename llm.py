import tool_functions as llmtools
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Configuration d'Ollama et de l'Agent IA (Llama 3.1)
llm = OllamaLLM(model="llama3.1", temperature=0)

# 1. MODIFICATION : Liste des nouveaux outils mis à disposition de l'agent
tools = [llmtools.get_machinistes, llmtools.get_machinistes_jour]

# Création du prompt pour guider l'agent
system_prompt = """Tu es un expert en ressources humaines et en planification de personnel.
Ton rôle est d'analyser les fichiers de planning, de comprendre les contraintes et d'aider à affecter les agents de manière optimale.

Tu as accès aux outils suivants : {tool_names}

Pour utiliser un outil, tu dois impérativement répondre au format JSON structuré décrit ci-dessous. 
Tu dois fournir un bloc JSON avec les clés "action" et "action_input".

Voici les outils à ta disposition :
{tools}

Quand tu as fini et que tu as la réponse finale, tu devez obligatoirement utiliser l'action "Final Answer" :
- action: "Final Answer"
- action_input: "Ta réponse en français ici"
"""

# Prompt avec historique de conversation et bloc-notes de l'agent
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt), 
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}\n\n{agent_scratchpad}"),
])

# On construit l'agent en lui donnant les outils mis à jour
agent = create_structured_chat_agent(llm, tools, prompt)

# On l'exécute ! 
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,  # pour voir le raisonnement
    handle_parsing_errors=True
)


question_test = "Quels machinistes peuvent conduire la ligne 66 ?"

print("--- Lancement du test de l'agent ---")


reponse = agent_executor.invoke({"input": question_test})

print("\n--- Réponse finale de l'agent ---")
print(reponse["output"])