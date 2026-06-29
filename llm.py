import tool_functions as llmtools
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool


# Configuration d'Ollama et de l'Agent IA

llm = OllamaLLM(model="llama3", temperature=0)

# Liste des outils mis à disposition de l'agent
tools = [llmtools.lire_planning_excel]

# Création du prompt pour guider l'agent
system_prompt = """Tu es un expert en ressources humaines et en planification de personnel.
Ton rôle est d'analyser les fichiers de planning, de comprendre les contraintes et d'aider à affecter les agents de manière optimale.

Tu as accès aux outils suivants : {tool_names}

Pour utiliser un outil, tu dois impérativement répondre au format JSON structuré décrit ci-dessous. 
Tu dois fournir un bloc JSON avec les clés "action" et "action_input".

Voici les outils à ta disposition :
{tools}

Quand tu as fini et que tu as la réponse finale, tu dois obligatoirement utiliser l'action "Final Answer" :
- action: "Final Answer"
- action_input: "Ta réponse en français ici"
"""


#on fait un joli prompt avec notre prompt de base auquel on ajoute de la mémoire pour qu'il garde l'historique de la conversation, inupt est notre question (humaine) et le blocnotes c'est là où l'agent écrit ses pensées
prompt = ChatPromptTemplate.from_messages([("system", system_prompt), MessagesPlaceholder(variable_name="chat_history", optional=True),("human", "{input}\n\n{agent_scratchpad}"),])

#on construit l'agent en lui donnant tout
agent = create_structured_chat_agent(llm, tools, prompt)

# on l"exécute ! 
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,  # pour voir le raisonnement
    handle_parsing_errors=True
)

