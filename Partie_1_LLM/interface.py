import llm as llm_module
import streamlit as st

agent_executor = llm_module.agent_executor

st.header("Planification des services")
st.subheader("RATP Cap - Boucles Nord de Seine")

# Création d'une liste de dictionnaires. 
# Comme le programme est réexécuté à chaque interaction, on ne peut pas initialiser une simple liste Python,
# on doit l'initialiser dans une structure appelée session_state.
if "history" not in st.session_state:
    st.session_state.history = []

prompt = st.chat_input("Posez une question...")
if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})

for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt :
    with st.spinner("L'IA réfléchit..."):
        reponse = agent_executor.invoke({"input": prompt, "chat_history": st.session_state.history})
    output = reponse["output"]
    st.session_state.history.append({"role": "assistant", "content": output})

    message = st.session_state.history[-1]
    with st.chat_message(message["role"]):
        st.write(message["content"])
