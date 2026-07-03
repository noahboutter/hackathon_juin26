import streamlit as st

st.set_page_config(layout="wide")

st.image("logo_ratp.svg", width=300)
st.header("Planification des services")

st.subheader("Affectations du 12/01/2024")
st.write("Sur chaque ligne, on indique le numéro de service et le numéro d'agent qui le réalise.")

lignes = [66, 74, 85, 137, 138, 140, 166, 174, 175, 177, 178, 235, 237, 238, 274, 340, 363, 538, 753, 780, 818, 860]

affectations = [
    {"agent": "37", "service": "L066S001"},
    {"agent": "12", "service": "L066S002"},
    {"agent": "54", "service": "L066S003"},

    {"agent": "8", "service": "L074S001"},

    {"agent": "49", "service": "L085S001"},
    {"agent": "21", "service": "L085S002"},
    {"agent": "3", "service": "L085S003"},
    {"agent": "61", "service": "L085S004"},
    {"agent": "17", "service": "L085S005"},

    {"agent": "44", "service": "L137S001"},
    {"agent": "29", "service": "L137S002"},

    {"agent": "6", "service": "L138S001"},
    {"agent": "58", "service": "L138S002"},
    {"agent": "24", "service": "L138S003"},
    {"agent": "42", "service": "L138S004"},

    # Ligne 140 : 0 service

    {"agent": "15", "service": "L166S001"},
    {"agent": "52", "service": "L166S002"},
    {"agent": "10", "service": "L166S003"},
    {"agent": "63", "service": "L166S004"},
    {"agent": "27", "service": "L166S005"},
    {"agent": "39", "service": "L166S006"},

    {"agent": "1", "service": "L174S001"},
    {"agent": "46", "service": "L174S002"},

    {"agent": "33", "service": "L175S001"},

    {"agent": "57", "service": "L177S001"},
    {"agent": "14", "service": "L177S002"},
    {"agent": "41", "service": "L177S003"},

    {"agent": "20", "service": "L178S001"},
    {"agent": "55", "service": "L178S002"},
    {"agent": "9", "service": "L178S003"},
    {"agent": "36", "service": "L178S004"},
    {"agent": "62", "service": "L178S005"},
    {"agent": "5", "service": "L178S006"},

    {"agent": "48", "service": "L235S001"},
    {"agent": "18", "service": "L235S002"},

    # Ligne 237 : 0 service

    {"agent": "31", "service": "L238S001"},
    {"agent": "59", "service": "L238S002"},
    {"agent": "11", "service": "L238S003"},

    {"agent": "45", "service": "L274S001"},

    {"agent": "25", "service": "L340S001"},
    {"agent": "60", "service": "L340S002"},
    {"agent": "7", "service": "L340S003"},
    {"agent": "34", "service": "L340S004"},
    {"agent": "53", "service": "L340S005"},

    {"agent": "19", "service": "L363S001"},
    {"agent": "47", "service": "L363S002"},

    {"agent": "4", "service": "L538S001"},
    {"agent": "56", "service": "L538S002"},
    {"agent": "23", "service": "L538S003"},
    {"agent": "38", "service": "L538S004"},

    {"agent": "30", "service": "L753S001"},
    {"agent": "64", "service": "L753S002"},
    {"agent": "16", "service": "L753S003"},
    {"agent": "51", "service": "L753S004"},
    {"agent": "2", "service": "L753S005"},
    {"agent": "43", "service": "L753S006"},

    {"agent": "28", "service": "L780S001"},

    {"agent": "40", "service": "L818S001"},
    {"agent": "13", "service": "L818S002"},
    {"agent": "50", "service": "L818S003"},

    {"agent": "22", "service": "L860S001"},
    {"agent": "35", "service": "L860S002"},
]

services_NA = ["L140S001", "L237S001"]
agents_NA = ["26", "32"]

n_cols = 5

for i in range(0, len(lignes), n_cols):
    cols = st.columns(n_cols)

    for col, ligne in zip(cols, lignes[i:i+n_cols]):
        with col:
            if ligne in [753, 780, 818, 860]:
                st.write(f"**{ligne}**")
            else:
                st.image(f"https://www.ratp.fr/sites/default/files/lines-assets/picto/busratp/picto_busratp_ligne-{ligne}.svg", width=50)
            st.table([[a["service"], a["agent"]] for a in affectations if int(a["service"][1:4]) == ligne])

st.subheader("Lacunes d'affectation")

cols = st.columns(2)
with cols[0]:
    st.write("**Services non affectés**")
    st.table(services_NA)
with cols[1]:
    st.write("**Agents non affectés**")
    st.table(agents_NA)
