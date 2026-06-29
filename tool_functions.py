import pandas as pd
from langchain.tools import tool
import platform
import datetime

def lire_planning_excel_df(chemin_fichier: str):
    """ Utile pour lire le contenu du fichier Excel """
    if platform.system() == "Darwin":
        chemin_fichier.replace("/", "\\")
    df = pd.read_excel(chemin_fichier)
    df.rename(inplace=True, columns={'Identifiant':'id', 'Heure de fin':'H_fin', 'Heure de début':'H_deb', 'Type de journée':'type_jour', 'Code journée' : 'code_jour'})
    return df

planning_df = lire_planning_excel_df("data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")
non_affecte_dfs = [lire_planning_excel_df(f"data/Services_Agents_non_affectés_le_1{i}_01_2026.xlsx") for i in range(2, 7)]

@tool
def lire_planning_excel(chemin_fichier: str) -> str :
    """ Utile pour lire le contenu du fichier Excel """
    if platform.system() == "Darwin":
        chemin_fichier.replace("/", "\\")
    return pd.read_excel(chemin_fichier).to_string(index=False)

#planning = lire_planning_excel("data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")

def get_machinistes(ligne, df=planning_df):
    """Renvoie la liste des machinistes pour une ligne donnée"""
    machinistes = []
    for id in df.index:
        if str(ligne) in str(df.loc[id, "Qualification : Connaissance de ligne"]):
            machinistes.append(id)
    return machinistes

def get_fitting_agents(day: str, deb="00:00", fin="23:59", lines=None) -> str:
    day_index = datetime(day).day % 10 - 2
    deb_time = datetime(deb)
    fin_time = datetime(fin)
    df = non_affecte_dfs[day_index]
    mask = (datetime(df['Début']) > deb_time) & (datetime(df["Fin'"]) < fin_time) & (int(df['Service'].str[1:3]) in lines)
    return df[mask]['Service'].to_string()




print(get_machinistes(24))


