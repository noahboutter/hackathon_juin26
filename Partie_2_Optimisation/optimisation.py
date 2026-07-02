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
    - "DISPO AM" si le service commence à partir de 14h00 ;
    - "DISPO M" si le service finit avant ou à 14h00 ;
    - "DISPO N" si le service finit après 22h ;
    - "DISPO" sans précision horaire.

    La fonction renvoie uniquement la matrice D.
    Elle ne renvoie pas les listes d'association entre identifiants réels
    et indices i ou j.
    """
    df_mach = (pd.read_excel(chemin_fichier_mach))[['Identifiant', 'Qualification : Connaissance de ligne', day]]
    df_serv = (pd.read_excel(chemin_fichier_serv)) [['Service', 'Début', 'Fin']]
    df_mach['qualification'] = df_mach['Qualification : Connaissance de ligne'].apply(
    lambda y: [int(x) for x in re.findall(r"\d+", str(y))] if pd.notna(y) else []
)
    N = len(df_mach['Identifiant'])
    P = len(df_serv['Service'])
    D = np.zeros((N,P), dtype=np.int8)
    for i in range(N):
        for j in range(P):
            service = df_serv['Service'].iloc[j]

            if pd.isna(service):
                continue

            ligne_service = int(str(service)[1:4])
            if ligne_service not in df_mach['qualification'].iloc[i]:
                continue
            if pd.isna(df_mach[day].iloc[i]) or (df_mach[day].iloc[i] in STATUTS_DISPONIBLE):
                D[i, j] = 1
            elif re.search("DISPO AM",df_mach[day].iloc[i]) and to_time(df_serv['Début'].iloc[j]) >= to_time(datetime.datetime.strptime("12:00", format="%H:%M")):
                D[i,j] = 1
            elif re.search("DISPO M",df_mach[day].iloc[i]) and to_time(df_serv['Fin'].iloc[j]) <= to_time(datetime.datetime.strptime("14:00", format="%H:%M")):
                D[i,j] = 1
            elif re.search("DISPO N",df_mach[day].iloc[i]) and (to_time(df_serv['Fin'].iloc[j]) >= to_time(datetime.datetime.strptime("22:00", format="%H:%M")) or to_time(df_serv['Fin'].iloc[j]) <= to_time(datetime.datetime.strptime("05:00", format="%H:%M"))):
                D[i,j] = 1
            elif re.search(r"\bDISPO\b(?!\s*(AM|M|N)\b)", str(df_mach[day].iloc[i])):
                D[i,j] = 1
    return D
            

D = initialize_data("Partie_1_LLM/data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx", 'Partie_1_LLM/data/Services Agents non affectés le 12_01_2026.xlsx', '12/01/2026')

def type_service(df, j):
    pass

def W_initialize(chemin_fichier_pref: str,chemin_fichier_serv: str, dim, D):
    """
    Initialise la matrice de pondération W associée aux affectations machinistes-services.

    Paramètres
    ----------
    chemin_fichier_pref : str
        Chemin vers le fichier Excel contenant les préférences des machinistes.
        Le fichier doit contenir au minimum :
        - une colonne "préférence_ligne" ;
        - une colonne "préférence_horaire".

        La colonne "préférence_ligne" contient les numéros de lignes préférées,
        par exemple "123, 456, 789".
        L'ordre des lignes est interprété comme un ordre de préférence :
        les premières lignes sont les plus préférées.

        La colonne "préférence_horaire" contient les types d'horaires préférés,
        par exemple "MAT, AM, JOUR, COUP, NUIT".
        L'ordre est également interprété comme un ordre de préférence.

    chemin_fichier_serv : str
        Chemin vers le fichier Excel contenant les services.
        Le fichier doit contenir au minimum :
        - une colonne "Service" ;
        - une colonne "Début" ;
        - une colonne "Fin" ;
        - une colonne "Type", ou les informations nécessaires à la fonction type_service.

    dim : tuple
        Dimensions de la matrice W sous la forme (N, P), où :
        - N est le nombre de machinistes ;
        - P est le nombre de services.

    D : np.ndarray
        Matrice de faisabilité de dimension (N, P).
        D[i, j] vaut 1 si le machiniste i peut faire le service j,
        et 0 sinon.

    Retour
    ------
    W : np.ndarray
        Matrice de pondération de dimension (N, P).
        Pour les affectations faisables, W[i, j] est ajustée selon :
        - les préférences de ligne du machiniste ;
        - les préférences horaires du machiniste.

        Les affectations non faisables ne sont pas modifiées dans W.
        Elles doivent donc être interdites séparément par la matrice D
        dans le modèle d'optimisation.
    """

    coef_ligne = 1
    coef_horaire = 3
    coef_existence = 12
    W = coef_existence * np.ones(dim)
    df_pref = pd.read_excel(chemin_fichier_pref)
    df_serv = pd.read_excel(chemin_fichier_serv)
    N, P = dim
    for i in range(N):
        liste_ligne = [int(x) for x in re.findall(r"\d+", str(df_pref['préférence_ligne'].iloc[i]))] if pd.notna(df_pref['préférence_ligne'].iloc[i]) else []
        liste_horaire = [x for x in re.findall(r"JOUR|AM|MAT|COUP|NUIT", str(df_pref['préférence_horaire'].iloc[i]))] if pd.notna(df_pref['préférence_horaire'].iloc[i]) else []
        increment_ligne = 1 / (len(liste_ligne) if len(liste_ligne) != 0 else 1)
        increment_horaire = 1 / (len(liste_horaire) if len(liste_horaire) != 0 else 1)
        for j in range(P):
            if D[i,j] == 0:
                continue
            index_ligne = liste_ligne.index(int(df_serv['Service'].iloc[j][1:4]))
            index_horaire = liste_horaire.index(type_service(df_serv, j))
            W[i,j] += coef_ligne * (0.5 + ((len(liste_ligne) if len(liste_ligne) != 0 else 1) - index_ligne) * increment_ligne) + coef_horaire * coef_horaire * (0.5 + (len(liste_horaire) - index_horaire) * increment_horaire)
    return W

            


W = W_initialize("Partie_2_Optimisation/preferences_agents.xlsx", 'Partie_1_LLM/data/Services Agents non affectés le 12_01_2026.xlsx', (len(D), len(D[0])), D)

#W=np.ones((len(D),len(D[0])))

#on considère qu'on a D et W la 
from ortools.linear_solver import pywraplp
def opti():
    
    costs=W
    num_workers=len(D)
    num_tasks=len(D[0])
    y=np.zeros((num_workers,num_tasks))
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
        solver.Add(solver.Sum([x[i,j] for i in range(num_workers)]) <= 1)
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
                    y[i,j]=1
                    #print(f"Worker {i} assigned to task {j}." + f" Cost: {costs[i][j]}")
    #else:
        #print("No solution found.")
    return y
#x=opti()
def matrice_vers_dataframe(x, num_workers, num_tasks, identifiants, services):  
    #affectations = [[int(x[i, j].solution_value() > 0.5) for j in range(num_tasks)]for i in range(num_workers)]  
    df = pd.DataFrame(x, index=identifiants, columns=services)
    print (df) 
    return df


identifiants = pd.read_excel("Partie_1_LLM/data/Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")['Identifiant'].tolist() 
services = pd.read_excel('Partie_1_LLM/data/Services Agents non affectés le 12_01_2026.xlsx')['Service'].tolist()
num_workers=len(D)
num_tasks=len(D[0])
#df = matrice_vers_dataframe(x, num_workers, num_tasks, identifiants, services)

#df.to_excel("resultats.xlsx")

#on va retrouver qui fait des services de nuit et les aprèms
# on cherche les services de nuit et de l'aprèm

def tri_horaire (chemin_fichier_serv):
    df_serv = (pd.read_excel(chemin_fichier_serv)) [['Service', 'Début', 'Fin','Type']]
    P = len(df_serv['Service'])
    matin=df_serv[(df_serv['Fin']<str(14) )& (df_serv['Début']<str(14))]
    
    aprem=df_serv[(df_serv['Fin']<str(22) )& (df_serv['Début']>str(14))]
    nuit=df_serv[(df_serv['Fin']>str(22) )|(df_serv['Fin']<str(5))]
    coupure=df_serv[df_serv['Type']=='COUP']
    mixte=df_serv[(df_serv['Fin']>str(14) )& (df_serv['Début']<str(11))]
    return (matin,aprem,nuit,coupure,mixte)
    

