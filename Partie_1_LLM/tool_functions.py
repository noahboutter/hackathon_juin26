from pydoc import doc
import re
import os
import pandas as pd
from langchain_core.tools import tool


SERVICES_PATHS = [
    "data\\Services_Agents_non_affectes_le_12_01_2026.xlsx",
    "data\\Services_Agents_non_affectes_le_13_01_2026.xlsx",
    "data\\Services_Agents_non_affectes_le_14_01_2026.xlsx",
    "data\\Services_Agents_non_affectes_le_15_01_2026.xlsx",
    "data\\Services_Agents_non_affectes_le_16_01_2026.xlsx",
]

PLANNING_PATH = os.path.join("data", "Export_Planning_du_12_01_2026_au_16_01_2026.xlsx")

# Toutes les cases remplies dans l'emploi du temps signifient que le machiniste n'est pas disponible (repos, maladie, etc.),sauf pour les codes suivants, qui signifient que l'agent est disponible :
STATUTS_DISPONIBLE = {"ASSU", "CP_REPORT", "DDD", "DISPO", "DISPO AM", "DISPO AMPL", "DISPO M", "DISPO MX", "DISPO N"}

# S'il y a quelque chose comme "L140S004" dans la cellule = un service déjà affecté ce jour-là
RE_CODE_SERVICE = re.compile(r"^[A-Z]\d{2,3}S\d{3}$") # expression régulière pour détecter un code de service

# Variable globale contenant la liste des dates (cf fonction _load_planning)
DATE_COLS_CACHE = None

def _load_services() -> pd.DataFrame:
    """Charge le fichier des services à affecter en DataFrame pandas."""
    frames = []
    for path in SERVICES_PATHS:
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _load_planning() -> pd.DataFrame:
    """Charge le fichier planning des machinistes en DataFrame pandas.
    Met aussi à jour la variable globale `DATE_COLS_CACHE` avec la liste des colonnes de date."""
    global DATE_COLS_CACHE
    df = pd.read_excel(PLANNING_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    DATE_COLS_CACHE = [c for c in df.columns if re.match(r"\d{2}/\d{2}/\d{4}", str(c))]  # Les colonnes de date sont celles qui ressemblent à jj/mm/aaaa
    return df


def _ligne_extraite(code_service: str) -> str:
    """Renvoie le numéro de ligne du service.
    Les formats peuvent prendre deux formes : LnnnSnnn et MnnnSnnn (où n désigne un entier).
    Les trois premiers chiffres désignent le numéro de ligne, et les trois derniers le numéro de service.
    Exemple : L140S006 -> ligne 140 service 6"""

    m = code_service[1:4]
    return str(int(m))  # retire tous les zéros de tête


def _agent_connait_la_ligne(qualifications: str, ligne: str) -> bool:
    """Renvoie `True` si l'agent connaît la ligne donnée, `False` sinon.
    qualifications est la valeur brute de la cellule "Qualification : Connaissance de ligne" du planning (ex: "66, 74, 137, 140"), et `ligne` est un numéro de ligne
    déjà extrait 
    """
    if not isinstance(qualifications, str):
        return False
    lignes = [l.strip() for l in qualifications.split(",")] #Liste des lignes connues par l'agent
    return ligne in lignes


def _cellule_dispo(valeur) -> bool:
    """Un agent est considéré disponible ce jour-là si la cellule est vide ou ne contient que des statuts disponibles (pas de repos/congé/service déjà pris)."""
    
    # On s'occupe des cellules vides 
    if pd.isna(valeur) or str(valeur).strip() == "" or str(valeur).strip().lower() == "nan":
        return True
        
    # On gère les statuts multiples
    parts = [p.strip() for p in str(valeur).split(",")]
    
    # On cherche un statut pas disponible, si on trouve False sinon True
    for p in parts:
        if p not in STATUTS_DISPONIBLE:
            return False            
    return True


# Fonctions utilisées comme outils pour le LLM 

@tool
def compter_services_par_type(type_service: str, date: str = "") -> str:
    """Compte le nombre de services à affecter pour un type donné 
    
    type_service : 'MAT', 'AM', 'NUIT', 'COUP', 'JOUR'
    date (optionnel) : au format jj/mm/aaaa. Si précisée, compte uniquement pour ce jour. 
    Si vide, compte sur l'ensemble de la semaine."""
    try:
        type_service = type_service.strip().upper()
        
        if not date:
            # Par défaut on charge tout
            df = _load_services()
            periode_str = "sur l'ensemble de la période"
        else:
            # sinon on charge uniquement le fichier du jour
            date_fichier = date.replace("/", "_")
            fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None) #comme ça au lieu de renvoyer une erreur si y'a rien ça nous met none
            
            if not fichier_cible: #not none = True
                return f"Aucun fichier de services trouvé pour le {date}."
                
            df = pd.read_excel(fichier_cible)
            df.columns = [str(c).strip() for c in df.columns]
            periode_str = f"le {date}"
            
        nb = (df["Type"].astype(str).str.upper() == type_service).sum()
        total = len(df)
        return f"{nb} service(s) de type '{type_service}' sur {total} services à affecter au total {periode_str}."
    except Exception as e:
        return f"Erreur lors du comptage des services : {e}"


@tool
def lister_services_possibles_pour_agent(identifiant_agent: str, date: str = "") -> str:
    """ Donne la liste des services à affecter qu'un agent pourrait réaliser.
    
    identifiant_agent: l'identifiant numérique de l'agent (ex: '5').
    date (optionnel): au format jj/mm/aaaa. Si précisée, cherche uniquement les services possibles pour ce jour précis."""
    try:
        planning = _load_planning()
        agent_id = int(identifiant_agent)
        ligne_agent = planning.loc[planning["Identifiant"] == agent_id]
        
        if ligne_agent.empty:
            return f"Aucun agent trouvé avec l'identifiant {agent_id}."

        row_agent = ligne_agent.iloc[0]
        
        dates_a_verifier = set()
        if date: # si l'utilisateur a demandé une date précise
            if date not in DATE_COLS_CACHE:
                return f"Date '{date}' introuvable dans le planning."
            if _cellule_dispo(row_agent[date]):
                dates_a_verifier.add(date)
            else:
                return f"L'agent {agent_id} n'est pas disponible le {date} (statut : {row_agent[date]})."
        else: #sinon pour toute la période donnée
            for date_col in DATE_COLS_CACHE:
                if _cellule_dispo(row_agent[date_col]):
                    dates_a_verifier.add(date_col)
                    
        if not dates_a_verifier:
            return f"L'agent {agent_id} n'est disponible sur aucune date demandée/actuelle."

        # On charge les fichiers de services uniquement pour les jours où l'agent est dispo
        frames = []
        for d in dates_a_verifier:
            date_fichier = d.replace("/", "_")
            fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
            if fichier_cible:
                df_jour = pd.read_excel(fichier_cible)
                frames.append(df_jour)
                
        if not frames:
            return f"L'agent {agent_id} est disponible, mais aucun service n'est à pourvoir ces jours-là (fichiers vides ou introuvables)."

        services_jours_dispos = pd.concat(frames, ignore_index=True)

        # On vérifie que l'agent peut conduire la ligne 
        qualifs = row_agent["Qualification : Connaissance de ligne"]
        lignes_connues = {l.strip() for l in str(qualifs).split(",")}
        
        # On nettoie et on filtre
        services_jours_dispos = services_jours_dispos.dropna(subset=["Service"])
        services_jours_dispos["ligne"] = services_jours_dispos["Service"].astype(str).apply(_ligne_extraite)
        
        possibles = services_jours_dispos[services_jours_dispos["ligne"].isin(lignes_connues)]

        if possibles.empty:
            return (
                f"L'agent {agent_id} est disponible les {', '.join(sorted(dates_a_verifier))}, "
                f"mais il ne connaît pas les lignes des services à pourvoir ces jours-là (lignes connues : {', '.join(lignes_connues)})."
            )

        
        liste_services = possibles["Service"].tolist()
        return (
            f"L'agent {agent_id} est disponible aux dates suivantes : {', '.join(sorted(dates_a_verifier))}.\n"
            f"Il connaît les lignes : {', '.join(sorted(lignes_connues, key=lambda x:(len(x),x)))}.\n"
            f"{len(liste_services)} service(s) disponible(s) et compatible(s) : {', '.join(liste_services)}"
        )
    except Exception as e:
        return f"Erreur lors de la recherche des services pour l'agent {identifiant_agent} : {e}"

@tool
def lister_conducteurs_disponibles_pour_service(code_service: str, date: str = "") -> str:
    """À UTILISER UNIQUEMENT POUR UN SERVICE PRÉCIS ET NON POUR UNE LIGNE.
    Donne la liste des conducteurs disponibles pour un service donné (ex: 'L140S006'),
    en vérifiant la connaissance de ligne ET la disponibilité à la date du service.

    code_service: DOIT obligatoirement contenir la lettre 'S'. Ne jamais utiliser cet outil si l'utilisateur donne juste un numéro de ligne.
    date: DOIT obligatoirement être fournie, au format jj/mm/aaaa."""

    try:
        services = _load_services()
        planning = _load_planning()

        code_service = code_service.strip().upper()
        ligne = _ligne_extraite(code_service)
        if not ligne:
            return f"'{code_service}' ne ressemble pas à un code de service valide (format attendu: L140S006)."

        # On vérifie et formate la date fournie par l'utilisateur
        if date not in DATE_COLS_CACHE:
            try:
                date = pd.to_datetime(date, dayfirst=True).strftime("%d/%m/%Y")
            except Exception:
                pass

        # Si la date est introuvable dans le planning, on arrête
        if date not in DATE_COLS_CACHE:
            return (f"Date '{date}' introuvable dans le planning. "
                    f"Dates disponibles : {', '.join(DATE_COLS_CACHE)}")

        
        candidats = []
        for _, row in planning.iterrows():
            if _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne):
                if _cellule_dispo(row[date]):
                    candidats.append(str(row["Identifiant"]))

        if not candidats:
            return f"Aucun conducteur disponible et qualifié ligne {ligne} pour le service {code_service} le {date}."
        
        return (f"{len(candidats)} conducteur(s) disponible(s) et qualifié(s) ligne {ligne} "
                f"pour le service {code_service} le {date} : {', '.join(candidats)}")
                
    except Exception as e:
        return f"Erreur lors de la recherche de conducteurs pour {code_service} : {e}"

@tool
def lister_conducteurs_disponibles_pour_ligne(numero_ligne: str, date: str = "") -> str:
    """À UTILISER UNIQUEMENT QUAND L'UTILISATEUR PARLE D'UNE LIGNE ENTIÈRE (ex: 'ligne 66').
    Compte le nombre d'agents qualifiés ET disponibles pour conduire une ligne donnée.
    
    numero_ligne : UNIQUEMENT le numéro de la ligne en chiffres, ex '66', '140' ou '238'. (Ne jamais mettre de 'L' ou de 'S' ici).
    date au format jj/mm/aaaa (optionnel) : si non fournie, on prend la première date du planning."""
    try:
        planning = _load_planning()
        ligne = numero_ligne.strip()
 
        if not date:
            date = DATE_COLS_CACHE[0]
        elif date not in DATE_COLS_CACHE:
            try:
                date = pd.to_datetime(date, dayfirst=True).strftime("%d/%m/%Y")
            except Exception:
                pass
 
        if date not in DATE_COLS_CACHE:
            return (f"Date '{date}' introuvable dans le planning. "
                    f"Dates disponibles : {', '.join(DATE_COLS_CACHE)}")
 
        candidats = []
        for _, row in planning.iterrows():
            if _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne):
                if _cellule_dispo(row[date]):
                    candidats.append(str(row["Identifiant"]))

        if not candidats:
            return f"Aucun agent qualifié ligne {ligne} et disponible le {date}."
            
        return f"{len(candidats)} agent(s) qualifié(s) ligne {ligne} et disponible(s) le {date}. Ce sont les agents: {', '.join(candidats)}."
    except Exception as e:
        return f"Erreur lors de la recherche des agents disponibles pour la ligne {numero_ligne} : {e}"

@tool
def info_agent(identifiant_agent: str) -> str:
    """Donne les informations générales d'un agent : lignes connues et statut/affectation
    pour chaque jour de la semaine de planning.
    
    identifiant_agent: numéro, ex '5'   """
    try:
        planning = _load_planning()
        agent_id = int(identifiant_agent)
        ligne_agent = planning.loc[planning["Identifiant"] == agent_id]

        if ligne_agent.empty:
            return f"Aucun agent trouvé avec l'identifiant {agent_id}."
        
        row = ligne_agent.iloc[0]
        qualifs = row["Qualification : Connaissance de ligne"]
        jours = []

        for c in DATE_COLS_CACHE:
            val = row[c]
            val = "—" if pd.isna(val) or str(val).strip() == "" else str(val)
            jours.append(f"{c} : {val}")
        return f"Agent {agent_id} - lignes connues : {qualifs}\n" + "\n".join(jours)
    except Exception as e:
        return f"Erreur lors de la récupération des infos de l'agent {identifiant_agent} : {e}"


@tool
def compter_services_non_couverts(date: str = "") -> str:
    """Compte le nombre total de services présents dans le(s) fichier(s) des services non affectes 
    (= tous les services qui n'ont actuellement aucun conducteur assigné).
    
    date (optionnel) : au format jj/mm/aaaa. Si précisée, compte uniquement pour ce jour. Si vide, compte sur l'ensemble de la période."""
    try:
        if not date:
            # Par défaut : on compte sur toute la semaine
            df = _load_services()
            return f"{len(df)} service(s) restent non affectes au total sur l'ensemble de la période."
        else:
            # Sinon on cherche uniquement le fichier du jour
            date_fichier = date.replace("/", "_")
            fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
            
            if not fichier_cible:
                return f"Aucun fichier de services trouvé pour le {date}."

            df_jour = pd.read_excel(fichier_cible)
            return f"Il y a {len(df_jour)} service(s) non affecté(s) pour la journée du {date}."
            
    except Exception as e:
        return f"Erreur lors du comptage des services non couverts : {e}"
    
@tool
def compter_agents_par_statut(statut: str, date: str) -> str:
    """Compte ET liste les agents qui ont un statut spécifique (ex: 'CP', 'MAL', 'R') à une date donnée.
    date: format jj/mm/aaaa."""
    try:
        planning = _load_planning()
        statut = statut.strip().upper()
        
        if date not in DATE_COLS_CACHE:
            return f"Date '{date}' introuvable. Dates possibles : {', '.join(DATE_COLS_CACHE)}"
            
        agents_concernes = []
        for _, row in planning.iterrows():
            # Une cellule peut contenir plusieurs statuts 
            valeur_cellule = str(row[date]).upper()
            statuts_cellule = [s.strip() for s in valeur_cellule.split(",")]
            if statut in statuts_cellule:
                agents_concernes.append(str(row["Identifiant"]))
                
        if not agents_concernes:
            return f"Il n'y a aucun agent avec le statut '{statut}' le {date}."
            
        return f"Il y a {len(agents_concernes)} agent(s) avec le statut '{statut}' le {date} : {', '.join(agents_concernes)}."
    except Exception as e:
        return f"Erreur lors de la recherche par statut : {e}"

@tool
def lister_lignes_avec_penurie(date: str) -> str:
    """Liste les lignes où le nombre de services à couvrir dépasse le nombre d'agents disponibles et qualifiés pour cette date.
    date: format jj/mm/aaaa"""
    try:
        planning = _load_planning()
        
        if date not in DATE_COLS_CACHE:
            return f"Date '{date}' introuvable dans le planning."

        # On formate pour identifier le bon fichier
        date_fichier = date.replace("/", "_")
        fichier_cible = None
        
        # On cherche le fichier correspondant 
        for path in SERVICES_PATHS:
            if date_fichier in path:
                fichier_cible = path
                break
        
        if not fichier_cible:
            return f"Aucun fichier de services trouvé correspondant à la date du {date}."

        # On charge que le fichier du jour
        services_du_jour = pd.read_excel(fichier_cible)
        services_du_jour.columns = [str(c).strip() for c in services_du_jour.columns]
        
        if services_du_jour.empty:
            return f"Aucun service à couvrir le {date} (le fichier est vide)."

        # On supprime les lignes vides 
        services_du_jour = services_du_jour.dropna(subset=["Service"])
        services_du_jour["ligne"] = services_du_jour["Service"].astype(str).apply(_ligne_extraite)
        
        besoins_par_ligne = services_du_jour["ligne"].value_counts().to_dict()
        
        lignes_penurie = []
        for ligne, nb_services in besoins_par_ligne.items():
            # On compte les agents dispo et qualifiés pour la ligne
            agents_dispos = 0
            for _, row in planning.iterrows():
                if _cellule_dispo(row[date]) and _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne):
                    agents_dispos += 1
            
            # On regarde si c'est la crise
            if nb_services > agents_dispos:
                lignes_penurie.append(f"- Ligne {ligne} : {nb_services} service(s) pour {agents_dispos} agent(s) dispo(s).")
                
        if not lignes_penurie:
            return f"Aucune pénurie détectée pour le {date} : il y a assez de conducteurs potentiels pour chaque ligne."
            
        return f"Alerte pénurie le {date} pour {len(lignes_penurie)} ligne(s) :\n" + "\n".join(lignes_penurie)
        
    except Exception as e:
        return f"Erreur lors de l'analyse des pénuries : {e}"
    

@tool
def lister_services_sans_candidat(date: str) -> str:
    """Liste les services spécifiques pour lesquels absolument aucun agent qualifié ET disponible n'existe à cette date.
    date: format jj/mm/aaaa"""
    try:
        planning = _load_planning()
        
        if date not in DATE_COLS_CACHE:
            return f"Date '{date}' introuvable."

        # Rebelote on formate
        date_fichier = date.replace("/", "_")
        fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
        
        if not fichier_cible:
            return f"Aucun fichier de services trouvé pour le {date}."

        services_du_jour = pd.read_excel(fichier_cible)
        services_du_jour.columns = [str(c).strip() for c in services_du_jour.columns]
        
        services_critiques = []
        for _, srv in services_du_jour.iterrows():
            code = str(srv["Service"]).strip()
            ligne = _ligne_extraite(code)
            
            candidats = 0
            for _, row in planning.iterrows():
                if _cellule_dispo(row[date]) and _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne):
                    candidats += 1
            
            if candidats == 0:
                services_critiques.append(code)
                
        if not services_critiques:
            return f"Le {date}, tous les services ont au moins un candidat potentiel."
        return f"Il y a {len(services_critiques)} service(s) sans aucun candidat le {date} : {', '.join(services_critiques)}."
    except Exception as e:
        return f"Erreur : {e}"
    

@tool
def compter_services_par_ligne(numero_ligne: str, date: str = "") -> str:
    """Compte combien de services restent à affecter au total pour une ligne donnée.
    
    numero_ligne : UNIQUEMENT le numéro de la ligne en chiffres, ex '66', '140'.
    date (optionnel) : au format jj/mm/aaaa. Si précisée, compte uniquement pour ce jour. 
    Si vide, compte sur l'ensemble de la période"""
    try:
        # On nettoie le numéro de ligne
        numero_ligne = numero_ligne.strip().upper()
        if numero_ligne.startswith("L"):
            numero_ligne = numero_ligne[1:]
        try:
            numero_ligne = str(int(numero_ligne))
        except ValueError:
            pass 

        if not date:
            # idem par défaut on charge tout
            df = _load_services()
            periode_str = "sur l'ensemble de la période"
        else:
            # Sinon on charge uniquement le fichier du jour
            date_fichier = date.replace("/", "_")
            fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
            
            if not fichier_cible:
                return f"Aucun fichier de services trouvé pour le {date}."
                
            df = pd.read_excel(fichier_cible)
            df.columns = [str(c).strip() for c in df.columns]
            periode_str = f"le {date}"
            
        # On gère les parties vides
        df = df.dropna(subset=["Service"])
        
        # On extrait la ligne et on compte
        df["ligne"] = df["Service"].astype(str).apply(_ligne_extraite)
        nb = (df["ligne"] == numero_ligne).sum()
        
        return f"Il y a {nb} service(s) à affecter pour la ligne {numero_ligne} {periode_str}."
    except Exception as e:
        return f"Erreur : {e}"
    
@tool
def lister_services_par_date(date: str) -> str:
    """Liste tous les codes de services qui doivent être affectes à une date précise."""
    try:
        # C'est toujours la même on formate et on cherche
        date_fichier = date.replace("/", "_")
        fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
        
        if not fichier_cible:
            return f"Aucun service à affecter le {date} (fichier introuvable)."

        services_du_jour = pd.read_excel(fichier_cible)
        services_du_jour = services_du_jour.dropna(subset=["Service"]) #On gère le vide
        filtre = services_du_jour["Service"].astype(str).tolist()
        
        if not filtre:
            return f"Aucun service à affecter le {date} (fichier vide)."
            
        return f"{len(filtre)} service(s) à affecter le {date} : {', '.join(filtre)}"
    except Exception as e:
        return f"Erreur : {e}"
    
@tool
def resume_journee(date: str) -> str:
    """Fait une synthèse globale pour une journée : services à couvrir, agents dispos, et alertes.
    date: format jj/mm/aaaa"""
    try:
        planning = _load_planning()
        
        if date not in DATE_COLS_CACHE:
            return f"Date '{date}' introuvable."
            
        # On formate et on cherche
        date_fichier = date.replace("/", "_")
        fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
        
        if not fichier_cible:
            nb_services = 0
            services_du_jour = pd.DataFrame(columns=["Service"])
        else:
            services_du_jour = pd.read_excel(fichier_cible)
            services_du_jour.columns = [str(c).strip() for c in services_du_jour.columns]
            services_du_jour = services_du_jour.dropna(subset=["Service"])
            nb_services = len(services_du_jour)
        
        # Agents dispos 
        agents_dispos = sum(1 for _, row in planning.iterrows() if _cellule_dispo(row[date]))
        
        # Services sans candidats
        nb_sans_candidats = 0
        for _, srv in services_du_jour.iterrows():
            ligne = _ligne_extraite(str(srv["Service"]))
            candidats = sum(1 for _, row in planning.iterrows() if _cellule_dispo(row[date]) and _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne))
            if candidats == 0:
                nb_sans_candidats += 1
                
        return (f"--- SYNTHÈSE DU {date} ---\n"
                f"Services à couvrir : {nb_services}\n"
                f"Agents disponibles (toutes lignes) : {agents_dispos}\n"
                f"Services sans AUCUN candidat : {nb_sans_candidats}")
    except Exception as e:
        return f"Erreur de synthèse : {e}"
    
@tool
def taux_couverture_par_ligne(date: str) -> str:
    """Calcule le ratio de tension pour chaque ligne le jour J (Nb de services à affecter / Nb d'agents qualifiés et dispos).
    date: format jj/mm/aaaa"""
    try:
        planning = _load_planning()
        
        if date not in DATE_COLS_CACHE:
            return f"Date '{date}' introuvable."
            
        # On formate et on cherche
        date_fichier = date.replace("/", "_")
        fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
        
        if not fichier_cible:
            return f"Aucun fichier de services trouvé pour le {date}."

        services_du_jour = pd.read_excel(fichier_cible)
        services_du_jour.columns = [str(c).strip() for c in services_du_jour.columns]
        
        if services_du_jour.empty:
            return f"Aucun service prévu le {date}."

        #On compte les services à pourvoir    
        services_du_jour["ligne"] = services_du_jour["Service"].astype(str).apply(_ligne_extraite)
        besoins_par_ligne = services_du_jour["ligne"].value_counts().to_dict()
        
        #On compte le nombre d'agent dispo pour les services et on voit si c'est critique
        resultats = []
        for ligne, nb_services in besoins_par_ligne.items():
            agents_dispos = sum(1 for _, row in planning.iterrows() if _cellule_dispo(row[date]) and _agent_connait_la_ligne(row["Qualification : Connaissance de ligne"], ligne))
            
            ratio_text = f"Tension : {nb_services} service(s) pour {agents_dispos} agent(s) dispo(s)"
            if agents_dispos == 0:
                ratio_text += " CRITIQUE"
            elif nb_services > agents_dispos:
                ratio_text += " TENDU"
            else:
                ratio_text += " OK"
                
            resultats.append(f"- Ligne {ligne} => {ratio_text}")
            
        return f"Taux de couverture du {date} par ligne :\n" + "\n".join(resultats)
    except Exception as e:
        return f"Erreur de calcul des taux : {e}"

@tool
def filtrer_services_horaires(colonne: str, heure_limite: str, condition: str, date: str = "") -> str:
    """Filtre les services n'ayant pas de conducteur selon leur heure de Début ou de Fin.
    colonne : doit être exactement 'Début' ou 'Fin'.
    heure_limite : au format 'HH:MM' (ex: '08:00' ou '14:30').
    condition : doit être exactement 'avant' ou 'apres'.
    date (optionnel) : format 'jj/mm/aaaa'. Si vide, cherche sur toute la période.
    """
    try:
        
        # On formate et on cherche si on nous donne une date
        if date:
            date_fichier = date.replace("/", "_")
            fichier_cible = next((path for path in SERVICES_PATHS if date_fichier in path), None)
            if not fichier_cible:
                return f"Aucun fichier de services trouvé pour le {date}."
            df = pd.read_excel(fichier_cible)
        else:
            df = _load_services()

        df.columns = [str(c).strip() for c in df.columns]

        if colonne not in ['Début', 'Fin']:
            return "Le paramètre 'colonne' doit être 'Début' ou 'Fin'."

        # On nettoie et on formate l'heure
        def format_time(val):
            if pd.isna(val):
                return ""
            val_str = str(val).strip()
            if ":" not in val_str:
                return val_str
            heures, minutes = val_str.split(":")[:2]
            return f"{int(heures):02d}:{minutes[:2]}"  # ex: "4:30" -> "04:30"

        df['Heure_Format'] = df[colonne].apply(format_time)
        df = df[df['Heure_Format'] != ""] # On écarte les éventuelles cases vides

        # Si l'IA envoie "8:00" au lieu de "08:00" parce qu'on a eu des problèmes
        h_limite, m_limite = heure_limite.split(":")
        heure_limite = f"{int(h_limite):02d}:{m_limite[:2]}"

        df['Heure_Format'] = df[colonne].apply(format_time)
        df = df[df['Heure_Format'] != ""] # On gère les cases vides
        
        heure_limite = heure_limite.zfill(5) 

        # On filtre
        if condition.lower() == 'avant':
            df_filtre = df[df['Heure_Format'] < heure_limite]
        elif condition.lower() in ['apres', 'après']:
            df_filtre = df[df['Heure_Format'] > heure_limite]
        else:
            return "Le paramètre 'condition' doit être 'avant' ou 'apres'."

        services_trouves = df_filtre['Service'].astype(str).tolist()

        if not services_trouves:
            if date:
                return f"Le {date}, aucun service {condition} {heure_limite} pour l'heure de {colonne}."
            return f"Sur l'ensemble de la période, aucun service {condition} {heure_limite} pour l'heure de {colonne}."

        if date:
            return f"Le {date}, il y a {len(services_trouves)} service(s) {condition} {heure_limite} (heure de {colonne}) : {', '.join(services_trouves)}"
        return f"Sur toute la période, il y a {len(services_trouves)} service(s) {condition} {heure_limite} (heure de {colonne}) : {', '.join(services_trouves)}"

    except Exception as e:
        return f"Erreur lors du filtrage des horaires : {e}"


TOOLS = [
    compter_services_par_type,
    lister_services_possibles_pour_agent,
    lister_conducteurs_disponibles_pour_service,
    info_agent,
    compter_services_non_couverts,
    lister_conducteurs_disponibles_pour_ligne,
    compter_agents_par_statut,
    lister_lignes_avec_penurie,
    lister_services_sans_candidat,
    compter_services_par_ligne,
    lister_services_par_date,
    resume_journee,
    taux_couverture_par_ligne,
    filtrer_services_horaires
]
