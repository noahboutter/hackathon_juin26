#un super code arrive soon



import pandas as pd
import re
import numpy as np
import datetime


STATUTS_DISPONIBLE = {"ASSU", "CP_REPORT", "DDD","DISPO","DISPO AM", "DISPO AMPL", "DISPO M", "DISPO MX","DISPO N"}

def to_time(x):
    if isinstance(x, datetime.datetime):
        return x.time()
    elif isinstance(x, datetime.time):
        return x
    else:
        return datetime.datetime.strptime(str(x), "%H:%M").time()

def initialize_data(chemin_fichier_mach:str, chemin_fichier_serv, day: str):
    """
    Lit deux fichiers Excel :
    - un fichier contenant les machinistes ;
    - un fichier contenant les services.

    Le fichier des machinistes doit contenir au minimum :
    - une colonne "Identifiant" ;
    - une colonne "Qualification : Connaissance de ligne" ;
    - une colonne correspondant au jour donné dans l'argument day.

    Le fichier des services doit contenir au minimum :
    - une colonne "Service" ;
    - une colonne "Début" ;
    - une colonne "Fin".

    La fonction construit une matrice D de dimensions :
    nombre de machinistes × nombre de services.

    D[i, j] vaut 1 si le machiniste de la ligne i peut réaliser
    le service de la ligne j, et 0 sinon.

    Un machiniste peut réaliser un service si :
    - il connaît la ligne du service ;
    - et son statut du jour est compatible avec le service.

    Les statuts considérés comme disponibles sont :
    - une cellule vide / NaN ;
    - un statut appartenant à STATUTS_DISPONIBLE ;
    - "DISPO AM" si le service commence à partir de 12h00 ;
    - "DISPO M" si le service finit avant ou à 14h00 ;
    - "DISPO N" si le service commence à partir de 15h00 ;
    - "DISPO" sans précision horaire.

    La fonction renvoie uniquement la matrice D.
    Elle ne renvoie pas les listes d'association entre identifiants réels
    et indices i ou j.
    """
    df_mach = (pd.read_excel(chemin_fichier_mach))[['Identifiant', 'Qualification : Connaissance de ligne', day]]
    df_serv = (pd.read_excel(chemin_fichier_serv)) [['Service', 'Début', 'Fin']]
    df_mach['qualification'] = df_mach['Qualification : Connaissance de ligne'].apply(lambda y: [int(x) for x in re.findall(r"\d+", y)])
    N = len(df_mach['Identifiant'])
    P = len(df_serv['Service'])
    D = np.zeros((N,P), dtype=np.int8)
    for i in range(N):
        for j in range(P):
            if not (int(df_serv['Service'].iloc[j][1:4]) in df_mach['qualification'].iloc[i]):
                continue
            if pd.isna(df_mach[day].iloc[i]) or (df_mach[day].iloc[i] in STATUTS_DISPONIBLE):
                D[i, j] = 1
            elif re.search("DISPO AM",df_mach[day].iloc[i]) and to_time(df_serv['Début'].iloc[j]) >= to_time(datetime.datetime.strptime("12:00", format="%H:%M")):
                D[i,j] = 1
            elif re.search("DISPO M",df_mach[day].iloc[i]) and to_time(df_serv['Fin'].iloc[j]) <= to_time(datetime.datetime.strptime("14:00", format="%H:%M")):
                D[i,j] = 1
            elif re.search("DISPO N",df_mach[day].iloc[i]) and to_time(df_serv['Début'].iloc[j]) >= to_time(datetime.datetime.strptime("15:00", format="%H:%M")):
                D[i,j] = 1
            elif re.search(r"\bDISPO\b(?!\s*(AM|M|N)\b)", str(df_mach[day].iloc[i])):
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
