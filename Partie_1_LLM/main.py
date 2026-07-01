from langchain_core.messages import HumanMessage, AIMessage
import llm as llm_module

def main():
    print("Agent IA Planificateur")
    print("Posez vos questions en français. Tapez 'exit' pour quitter.\n")

    agent_executor = llm_module.agent_executor
    chat_history = []

    while True:
        try:
            question = input("Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFin de la session.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Fin de la session.")
            break

        try:
            reponse = agent_executor.invoke({
                "input": question,
                "chat_history": chat_history,
            })
            output = reponse["output"]
        except Exception as e:
            output = (
                "Une erreur est survenue pendant le traitement de votre question : "
                f"{e}\n"
            )

        print(f"\nAssistant > {output}\n")

        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=output))

        if len(chat_history) > 20: #pour pas saturer l'historique
            chat_history = chat_history[-20:]


if __name__ == "__main__":
    main()
