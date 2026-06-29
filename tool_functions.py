import pandas as pd
from langchain.tools import tool
import platform
import datetime

def lire_planning_excel_df(chemin_fichier: str):
    """ Utile pour lire le contenu du fichier Excel et le formater en DataFrame """
    if platform.system() == "Darwin":
        chemin_fichier = chemin_fichier.replace("/", "\\")
    
    df = pd.read_excel(chemin_fichier)
    # Renommer les colonnes de base pour faciliter les manipulations futures
    df.rename(inplace=True, columns={
        'Identifiant': 'id', 
        'Heure de fin': 'H_fin', 
        'Heure de début': 'H_deb', 
        'Type de journée': 'type_jour', 
        'Code journée': 'code_jour'
    })
    return df

# Chargement du DataFrame global
planning_df = lire_planning_excel_df("data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")
non_affecte_dfs = [lire_planning_excel_df(f"data/Services_Agents_non_affectés_le_1{i}_01_2026.xlsx") for i in range(2, 7)]

@tool
def get_machinistes(ligne: int) -> list:
    """Renvoie la liste des identifiants des machinistes qualifiés pour une ligne donnée."""
    global planning_df
    machinistes = []
    colonne_qualif = "Qualification : Connaissance de ligne"
    
    if colonne_qualif not in planning_df.columns:
        return f"Erreur : La colonne '{colonne_qualif}' n'existe pas."

    for _, row in planning_df.iterrows():
        qualifs_str = str(row[colonne_qualif])
        
        liste_lignes = [l.strip() for l in qualifs_str.split(',')]
        
        if str(ligne) in liste_lignes:
            machinistes.append(int(row['id'])) # On récupère l'id de l'agent, pas l'index Pandas
            
    return machinistes

def get_fitting_agents(day: str, deb="00:00", fin="23:59", lines=None) -> str:
    day_index = datetime(day).day % 10 - 2
    deb_time = datetime(deb)
    fin_time = datetime(fin)
    df = non_affecte_dfs[day_index]
    mask = (datetime(df['Début']) > deb_time) & (datetime(df["Fin'"]) < fin_time) & (int(df['Service'].str[1:3]) in lines)
    return df[mask]['Service'].to_string()



@tool
def get_machinistes_jour(jour: str) -> list:
    """Renvoie la liste des identifiants des machinistes qui n'ont rien de planifié (valeur vide) pour un jour donné (format 'JJ/MM/AAAA')."""
    global planning_df
    machinistes = []
    
    if jour not in planning_df.columns:
        return f"Erreur : La colonne pour le jour '{jour}' n'existe pas dans le planning."
        
    for _, row in planning_df.iterrows():
        # Si la cellule du jour est vide (NaN), l'agent est disponible / non affecté
        if pd.isnull(row[jour]):
            machinistes.append(int(row['id']))
            
    return machinistes