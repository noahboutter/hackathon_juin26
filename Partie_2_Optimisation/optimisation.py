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
            
    


#on considère qu'on a D et W la 
from ortools.linear_solver import pywraplp
def opti():
    costs=W
    num_workers=len(D)
    num_tasks=len(D[0])
    solver= pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return
    x={}
    for i in range(num_workers):
        for j in range(num_tasks):
            x[i,j]=solver.IntVar(0,1,"")
    #chaque machiniste a au plus 1 tâche
    for i in range (num_workers):
        solver.Add(solver.Sum([x[i,j] for j in range(num_tasks)]) <=1)
    #chaque tache est assignée a exactement un machiniste
    for j in range(num_tasks):
        solver.Add(solver.Sum([x[i,j] for i in range(num_workers)]) == 1)
    #chaque machiniste ne peut que faire les tâches pour lesquelles il est accrédité
    for i in range(num_workers):
        for j in range(num_tasks):
            if D[i][j]==0:
                solver.Add(x[i,j]==0)
    objective_terms=[]
    for i in range(num_workers):
        for j in range(num_tasks):
            objective_terms.append(costs[i][j]*x[i,j])
    solver.Maximize(solver.Sum(objective_terms))

    status=solver.Solve()
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        for i in range(num_workers):
            for j in range(num_tasks):
                # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
                if x[i, j].solution_value() > 0.5:
                    print(f"Worker {i} assigned to task {j}." + f" Cost: {costs[i][j]}")
    else:
        print("No solution found.")
