import pandas as pd
from langchain.tools import tool

@tool
def lire_planning_excel(chemin_fichier: str) -> str :
    """ Utile pour lire le contenu du fichier Excel """
    return pd.read_excel(chemin_fichier).to_string(index=False)