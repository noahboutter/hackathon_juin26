#un super code arrive soon



import pandas as pd
import re
import numpy as np
import datetime


STATUTS_DISPONIBLE = {"ASSU", "CP_REPORT", "DDD","DISPO","DISPO AM", "DISPO AMPL", "DISPO M", "DISPO MX","DISPO N"}


def initialize_data(chemin_fichier_mach:str, chemin_fichier_serv, day: str):
    """
    initialize_data(chemin_fichier_mach:str, chemin_fichier_serv, day: str)

    Cette fonction prend argument un chemin vers deux fichiers excel un listant les machinistes à affecter, et l'autre listant les services à affecter, et un jour de l'année au format "dd/mm/yyyy"
    Le fichier excel associé aux machinistes doit contenir a minima une colonne "Identifiant", une colonne "Qualification : Connaissance de ligne", et une colonne associe au jour day.
    Le fichier excel associé aux services doit contenir à minima une colonne "Service", une colonne "Début" et une colonne "Fin" donnant respectivement le numéro du service et ses horaires

    Cette fonction crée deux liste associant l'identifiant d'un machiniste à un identifiant i compris entre 0 et le nombre de machiniste, et une liste associant un service à un identifiant j

    Cette fonction tient en compte de la possibilité d'un travailleur de prendre son poste (Repos, maladie) et ignore toute affectation réalisée au préalable, et renvoie une matrice D tel que D[i,j] vaut 1 si le machiniste i peut réaliser le service j et 0 sinon 
    """
    df_mach = (pd.read_excel(chemin_fichier_mach))[['Identifiant', 'Qualification : Connaissance de ligne', day]]
    df_serv = (pd.read_excel(chemin_fichier_serv)) [['Service', 'Début', 'Fin']]
    df_mach['qualification'] = df_mach['Qualification : Connaissance de ligne'].apply(lambda y: [int(x) for x in re.findall(r"\d+", y)])
    N = len(df_mach['Identifiant'])
    P = len(df_serv['Service'])
    D = np.zeros((N,P), dtype=np.int8)
    for i in range(N):
        for j in range(N):
            verif = True
            if not (df_serv['Service'].iloc[j][1:4] in df_mach['qualification']):
                continue
            if pd.isna(df_mach[day].iloc[i]) or (df_mach[day].iloc[i] in STATUTS_DISPONIBLE):
                D[i, j] = 1
                verif = False
            elif re.search("DISPO AM",df_mach[day].iloc[i]) and df_serv['Début'].iloc[j] >= datetime.datetime.strptime("12:00", format="‰H:%M"):
                D[i,j] = 1
                verif = False
            elif re.search("DISPO M",df_mach[day].iloc[i]) and df_serv['Fin'].iloc[j] <= datetime.datetime.strptime("14:00", format="%H:%M"):
                D[i,j] = 1
                verif = False
            elif re.search("DISPO N",df_mach[day].iloc[i]) and df_serv['Début'].iloc[j] >= datetime.datetime.strptime("15:00", format="%H:%M"):
                D[i,j] = 1
                verif = False
            elif re.search("DISPO",df_mach[day].iloc[i]) and verif:
                D[i,j] = 1
    return D
            
    


