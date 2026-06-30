import re
import pandas as pd
from langchain_core.tools import tool



SERVICES_PATH = "data\\Services_Agents_non_affectés_le_12_01_2026.xlsx"
PLANNING_PATH = "data\\Export_Planning_du_12_01_2026_au_16_01_2026.xlsx"

# Statuts qui signifient explicitement "disponible, pas encore affecté"
STATUTS_DISPONIBLE = {"ASSU", "CP_REPORT", "DDD","DISPO","DISPO AM", "DISPO AMPL", "DISPO M", "DISPO MX","DISPO N"}

# Une cellule comme "L140S004" = un service déjà affecté ce jour-là
RE_CODE_SERVICE = re.compile(r"^[A-Z]\d{2,3}S\d{3}$")

DATE_COLS_CACHE = None  # détecté automatiquement au chargement


def _load_services() -> pd.DataFrame:
    df = pd.read_excel(SERVICES_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _load_planning() -> pd.DataFrame:
    global DATE_COLS_CACHE
    df = pd.read_excel(PLANNING_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    # Les colonnes de date sont celles dont le nom ressemble à jj/mm/aaaa
    DATE_COLS_CACHE = [c for c in df.columns if re.match(r"\d{2}/\d{2}/\d{4}", str(c))]
    return df


def _ligne_extraite(code_service: str) -> str:
    """'L140S006' -> '140' ; renvoie '' si le format ne matche pas."""
    m = re.match(r"^[A-Z](\d{2,3})S\d{3}$", str(code_service).strip())
    return m.group(1) if m else ""


def _agent_connait_la_ligne(qualifications: str, ligne: str) -> bool:
    if not isinstance(qualifications, str):
        return False
    lignes = [l.strip() for l in qualifications.split(",")]
    return ligne in lignes


def _cellule_dispo(valeur) -> bool:
    """Un agent est considéré disponible ce jour-là si la cellule est vide,
    ou ne contient que des statuts 'disponible' (pas de repos/congé/service déjà pris)."""
    # On découpe s'il y a plusieurs éléments (ex: "DISPO, ASSU")
    parts = [p.strip() for p in str(valeur).split(",")]
    for p in parts:
        if p not in STATUTS_DISPONIBLE:
            return False            
    return True


@tool
def compter_services_par_type(type_service: str) -> str:
    """Compte le nombre de services à affecter pour un type donné.
    type_service doit être l'un de : MAT, AM, SOI, NUIT (selon les valeurs réelles
    de la colonne Type du fichier services). Exemple : 'MAT' pour les services du matin."""
    try:
        df = _load_services()
        type_service = type_service.strip().upper()
        nb = (df["Type"].astype(str).str.upper() == type_service).sum()
        total = len(df)
        return f"{nb} service(s) de type '{type_service}' sur {total} services à affecter au total."
    except Exception as e:
        return f"Erreur lors du comptage des services : {e}"


@tool
def lister_services_possibles_pour_agent(identifiant_agent: str) -> str:
    """Donne la liste des services à affecter qu'un agent pourrait réaliser,
    en vérifiant d'abord ses jours de disponibilité, puis en cherchant les services 
    compatibles avec sa connaissance de ligne sur ces dates.
    identifiant_agent : l'identifiant numérique de l'agent (ex: '5')."""
    try:
        planning = _load_planning()
        services = _load_services()

        agent_id = int(identifiant_agent)
        ligne_agent = planning.loc[planning["Identifiant"] == agent_id]
        if ligne_agent.empty:
            return f"Aucun agent trouvé avec l'identifiant {agent_id}."

        row_agent = ligne_agent.iloc[0]
        
        dates_disponibles = set()
        for date_col in DATE_COLS_CACHE:
            if _cellule_dispo(row_agent[date_col]):
                dates_disponibles.add(date_col)
        
        if not dates_disponibles:
            return f"L'agent {agent_id} n'est disponible sur aucune date du planning actuel."

        services["date_str"] = pd.to_datetime(services["Date"]).dt.strftime("%d/%m/%Y")
        services_jours_dispos = services[services["date_str"].isin(dates_disponibles)].copy()

        if services_jours_dispos.empty:
            return f"L'agent {agent_id} est disponible les {', '.join(sorted(dates_disponibles))}, mais aucun service n'est à pourvoir ces jours-là."

        
        qualifs = row_agent["Qualification : Connaissance de ligne"]
        lignes_connues = {l.strip() for l in str(qualifs).split(",")}
        
        services_jours_dispos["ligne"] = services_jours_dispos["Service"].apply(_ligne_extraite)
        possibles = services_jours_dispos[services_jours_dispos["ligne"].isin(lignes_connues)]

        if possibles.empty:
            return (
                f"L'agent {agent_id} est disponible les {', '.join(sorted(dates_disponibles))}, "
                f"mais il ne connaît pas les lignes des services à pourvoir ces jours-là (lignes connues : {', '.join(lignes_connues)})."
            )

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
    """Donne la liste des conducteurs disponibles pour un service donné (ex: 'L140S006'),
    en vérifiant la connaissance de ligne ET la disponibilité à la date du service.
    date au format jj/mm/aaaa, optionnel : si non fournie, on prend la date du service
    trouvée dans le fichier des services."""
    try:
        services = _load_services()
        planning = _load_planning()

        code_service = code_service.strip().upper()
        ligne = _ligne_extraite(code_service)
        if not ligne:
            return f"'{code_service}' ne ressemble pas à un code de service valide (format attendu: L140S006)."

        if not date:
            ligne_service = services[services["Service"].astype(str).str.upper() == code_service]
            if not ligne_service.empty:
                d = ligne_service.iloc[0]["Date"]
                date = pd.to_datetime(d).strftime("%d/%m/%Y")

        if date and date not in DATE_COLS_CACHE:
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
def info_agent(identifiant_agent: str) -> str:
    """Donne les informations générales d'un agent : lignes connues et statut/affectation
    pour chaque jour de la semaine de planning. identifiant_agent : ex '5'."""
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
        return f"Agent {agent_id} — lignes connues : {qualifs}\n" + "\n".join(jours)
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


TOOLS = [
    compter_services_par_type,
    lister_services_possibles_pour_agent,
    lister_conducteurs_disponibles_pour_service,
    info_agent,
    compter_services_non_couverts,
]
