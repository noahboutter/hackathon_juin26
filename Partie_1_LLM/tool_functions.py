from pydoc import doc
import re
import pandas as pd
from langchain_core.tools import tool



SERVICES_PATHS = [
    "data\\Services_Agents_non_affectés_le_12_01_2026.xlsx",
    "data\\Services_Agents_non_affectés_le_13_01_2026.xlsx",
    "data\\Services_Agents_non_affectés_le_14_01_2026.xlsx",
    "data\\Services_Agents_non_affectés_le_15_01_2026.xlsx",
    "data\\Services_Agents_non_affectés_le_16_01_2026.xlsx",
]

PLANNING_PATH = "data\\Export_Planning_du_12_01_2026_au_16_01_2026.xlsx"

# Toutes les cases remplies dans l'emploi du temps signifient que le machiniste n'est pas disponible (repos, maladie, etc.),
# sauf pour les codes suivants, qui signifient que l'agent est disponible :
STATUTS_DISPONIBLE = {"ASSU", "CP_REPORT", "DDD", "DISPO", "DISPO AM", "DISPO AMPL", "DISPO M", "DISPO MX", "DISPO N"}

# Une cellule comme "L140S004" = un service déjà affecté ce jour-là
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
    A aussi pour effet de mettre à jour la variable globale `DATE_COLS_CACHE` avec la liste des colonnes de date."""
    global DATE_COLS_CACHE
    df = pd.read_excel(PLANNING_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    # Les colonnes de date sont celles dont le nom ressemble à jj/mm/aaaa
    DATE_COLS_CACHE = [c for c in df.columns if re.match(r"\d{2}/\d{2}/\d{4}", str(c))]
    return df


def _ligne_extraite(code_service: str) -> str:
    """Renvoie le numéro de ligne du service.\\
    Les formats peuvent prendre deux formes : LnnnSnnn et MnnnSnnn (où n désigne un entier).
    Les trois premiers chiffres désignent le numéro de ligne, et les trois derniers le numéro de service.\\
    Exemple : L140S006 -> ligne 140 service 6"""
    m = code_service[1:4]
    if m[0] == "0":
        m = m[1:]
    return m


def _agent_connait_la_ligne(qualifications: str, ligne: str) -> bool:
    """Renvoie `True` si l'agent connaît la ligne donnée, `False` sinon."""
    # Vérifie le type de `qualifications` pour éviter les erreurs
    if not isinstance(qualifications, str):
        return False
    # Liste des lignes connues par l'agent
    lignes = [l.strip() for l in qualifications.split(",")]
    return ligne in lignes


def _cellule_dispo(valeur) -> bool:
    """Un agent est considéré disponible ce jour-là si la cellule est vide,
    ou ne contient que des statuts 'disponible' (pas de repos/congé/service déjà pris)."""
    # On découpe s'il y a plusieurs éléments (ex: "DISPO, ASSU")
    parts = [p.strip() for p in str(valeur).split(",")]
    # S'il y a un élément qui indique que l'agent n'est pas disponible, on renvoie False
    for p in parts:
        if p not in STATUTS_DISPONIBLE:
            return False            
    return True


# ====== Fonctions utilisées comme outils pour le LLM ======

@tool
def compter_services_par_type(type_service: str) -> str:
    """Compte le nombre de services à affecter pour un type donné.
    `type_service` doit être l'un de : MAT, AM, SOI, NUIT (selon les valeurs réelles
    de la colonne Type du fichier services). Exemple : 'MAT' pour les services du matin."""
    try:
        df = _load_services()
        type_service = type_service.strip().upper()
        nb = (df["Type"].astype(str).str.upper() == type_service).sum() # Comptage du nombre de services correspondant au type
        total = len(df)
        return f"{nb} service(s) de type '{type_service}' sur {total} services à affecter au total."
    except Exception as e:
        return f"Erreur lors du comptage des services : {e}"


@tool
def lister_services_possibles_pour_agent(identifiant_agent: str) -> str:
    """Donne la liste des services à affecter qu'un agent pourrait réaliser,
    en vérifiant d'abord ses jours de disponibilité, puis en cherchant les services 
    compatibles avec sa connaissance de ligne sur ces dates.
    
    :identifiant_agent: l'identifiant numérique de l'agent (ex: '5')."""
    try:
        planning = _load_planning()
        services = _load_services()

        agent_id = int(identifiant_agent)
        ligne_agent = planning.loc[planning["Identifiant"] == agent_id]
        if ligne_agent.empty:
            return f"Aucun agent trouvé avec l'identifiant {agent_id}."

        row_agent = ligne_agent.iloc[0]
        
        # Disponibilités de l'agen
        dates_disponibles = set()
        for date_col in DATE_COLS_CACHE:
            if _cellule_dispo(row_agent[date_col]):
                dates_disponibles.add(date_col)
        
        if not dates_disponibles:
            return f"L'agent {agent_id} n'est disponible sur aucune date du planning actuel."

        # Services disponibles lors des disponibilités de l'agent
        services["date_str"] = pd.to_datetime(services["Date"]).dt.strftime("%d/%m/%Y")
        services_jours_dispos = services[services["date_str"].isin(dates_disponibles)].copy()

        if services_jours_dispos.empty:
            return f"L'agent {agent_id} est disponible les {', '.join(sorted(dates_disponibles))}, mais aucun service n'est à pourvoir ces jours-là."

        # Vérification des lignes que peut conduire l'agent
        qualifs = row_agent["Qualification : Connaissance de ligne"]
        lignes_connues = {l.strip() for l in str(qualifs).split(",")}
        
        services_jours_dispos["ligne"] = services_jours_dispos["Service"].apply(_ligne_extraite)
        possibles = services_jours_dispos[services_jours_dispos["ligne"].isin(lignes_connues)]

        if possibles.empty:
            return (
                f"L'agent {agent_id} est disponible les {', '.join(sorted(dates_disponibles))}, "
                f"mais il ne connaît pas les lignes des services à pourvoir ces jours-là (lignes connues : {', '.join(lignes_connues)})."
            )

        # Résultat final
        liste_services = possibles["Service"].tolist()
        return (
            f"L'agent {agent_id} est disponible aux dates suivantes : {', '.join(sorted(dates_disponibles))}.\n"
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

    code_service: DOIT obligatoirement contenir la lettre 'S' (format attendu: L140S006, L066S012). Ne jamais utiliser cet outil si l'utilisateur donne juste un numéro de ligne.
    date (optionnel): au format jj/mm/aaaa ; si non fournie, on prend la date du service
    trouvée dans le fichier des services."""
    try:
        services = _load_services()
        planning = _load_planning()

        code_service = code_service.strip().upper()
        ligne = _ligne_extraite(code_service)
        if not ligne:
            return f"'{code_service}' ne ressemble pas à un code de service valide (format attendu: L140S006)."

        # Si on n'a pas la date en argument, on la cherche dans le fichier des services
        if not date:
            ligne_service = services[services["Service"].astype(str).str.upper() == code_service]
            if not ligne_service.empty:
                d = ligne_service.iloc[0]["Date"]
                date = pd.to_datetime(d).strftime("%d/%m/%Y")

        if date and (date not in DATE_COLS_CACHE):
            # tentative de reformattage
            try:
                date = pd.to_datetime(date, dayfirst=True).strftime("%d/%m/%Y")
            except Exception:
                pass

        if not date or date not in DATE_COLS_CACHE:
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
            
        return f"{len(candidats)} agent(s) qualifié(s) ligne {ligne} et disponible(s) le {date} : {', '.join(candidats)}."
    except Exception as e:
        return f"Erreur lors de la recherche des agents disponibles pour la ligne {numero_ligne} : {e}"

@tool
def info_agent(identifiant_agent: str) -> str:
    """Donne les informations générales d'un agent : lignes connues et statut/affectation
    pour chaque jour de la semaine de planning.
    
    :identifiant_agent: ex '5'   """
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
def compter_services_non_couverts() -> str:
    """Compte le nombre total de services présents dans le fichier des services non affectés
    (= tous les services qui n'ont actuellement aucun conducteur assigné)."""
    try:
        df = _load_services()
        return f"{len(df)} service(s) restent non affectés au total."
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
            # Une cellule peut contenir plusieurs statuts séparés par des virgules
            valeur_cellule = str(row[date]).upper()
            statuts_cellule = [s.strip() for s in valeur_cellule.split(",")]
            if statut in statuts_cellule:
                agents_concernes.append(str(row["Identifiant"]))
                
        if not agents_concernes:
            return f"Il n'y a aucun agent avec le statut '{statut}' le {date}."
            
        return f"Il y a {len(agents_concernes)} agent(s) avec le statut '{statut}' le {date} : {', '.join(agents_concernes)}."
    except Exception as e:
        return f"Erreur lors de la recherche par statut : {e}"



TOOLS = [
    compter_services_par_type,
    lister_services_possibles_pour_agent,
    lister_conducteurs_disponibles_pour_service,
    info_agent,
    compter_services_non_couverts,
    lister_conducteurs_disponibles_pour_ligne,
    compter_agents_par_statut,
]
