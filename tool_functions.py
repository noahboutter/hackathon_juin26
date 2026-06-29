import pandas as pd
from langchain.tools import tool
import platform

def lire_planning_excel_df(chemin_fichier: str):
    """ Utile pour lire le contenu du fichier Excel """
    if platform.system() == "Darwin":
        chemin_fichier.replace("/", "\\")
    df = pd.read_excel(chemin_fichier)
    df.rename(inplace=True, columns={'Identifiant':'id', 'Heure de fin':'H_fin', 'Heure de début':'H_deb', 'Type de journée':'type_jour', 'Code journée' : 'code_jour'})
    return df

planning_df = lire_planning_excel_df("data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")
non_affecte_dfs = [lire_planning_excel_df(f"Services Agents non affectés le 1{i}_01_2026.xlsx") for i in range(2, 7)]

@tool
def lire_planning_excel(chemin_fichier: str) -> str :
    """ Utile pour lire le contenu du fichier Excel """
    if platform.system() == "Darwin":
        chemin_fichier.replace("/", "\\")
    return pd.read_excel(chemin_fichier).to_string(index=False)

#planning = lire_planning_excel("data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")

@tool
def get_machinistes(ligne, df=planning_df):
    """Renvoie la liste des machinistes pour une ligne donnée"""
    machinistes = []
    for id in df.index:
        if str(ligne) in str(df.loc[id, "Qualification : Connaissance de ligne"]):
            machinistes.append(id)
    return machinistes

#print(get_machinistes(24))
def get_machinistes_jour(jour,df=planning_df):
    """renvoie la liste des machinistes pour un jour donné"""
    machinistes=[]
    for id in df.index:
        if pd.isnull(df.loc[id,jour]):
            machinistes.append(id)
    return machinistes

#print(get_machinistes_jour("12/01/2026"))


