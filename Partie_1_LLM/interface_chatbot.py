from llm import agent_executor
import streamlit as st

st.image("logo_ratp.svg", width=300)
st.header("Planification des services")

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
