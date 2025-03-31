"""
Sous-module 'parser.py' - Traitement et analyse des données ferroviaires.

Ce sous-module contient plusieurs fonctions permettant de traiter des données
ferroviaires relatives aux sillons de train, aux correspondances, aux chantiers,
aux machines, et aux agents. Il permet d'initialiser des dictionnaires avec ces
informations et d'écrire les résultats sous forme de fichiers Excel pour une
analyse ultérieure.

Fonctions principales :
-----------------------
- init_dict_t_a(df_sillons_arr: pd.DataFrame) -> dict :
    Initialise un dictionnaire des horaires d’arrivée des trains.

- init_dict_t_d(df_sillons_dep: pd.DataFrame) -> dict :
    Initialise un dictionnaire des horaires de départ des trains.

- init_dict_correspondances(df_correspondance: pd.DataFrame) -> dict :
    Crée un dictionnaire des correspondances entre trains d’arrivée et de départ.

- init_dict_limites_chantiers(
    df_chantiers: pd.DataFrame,
    df_sillon_dep: pd.DataFrame,
    dernier_depart: float
    ) -> dict :
    Génère un dictionnaire des indisponibilités des chantiers en fonction du temps.

- init_dict_limites_machines(
    df_machines: pd.DataFrame,
    df_sillon_dep: pd.DataFrame,
    dernier_depart: float
    ) -> dict :
    Génère un dictionnaire des indisponibilités des machines en fonction du temps.

- init_dict_limites_voies(df_chantiers: pd.DataFrame) -> dict :
    Détermine le nombre de voies disponibles par chantier.

- init_dict_nombre_max_agents_sur_roulement(df_roulement_agent: pd.DataFrame) -> dict :
    Initialise un dictionnaire du nombre maximal d’agents disponibles sur chaque roulement.

- init_dict_roulements_operants_sur_tache(df_roulement_agent: pd.DataFrame) -> dict :
    Associe les roulements aux types de tâches qu'ils peuvent effectuer.

- init_dicts_heure_debut_roulement(
    df_roulement_agent: pd.DataFrame,
    first_arr: int, last_dep: int
    ) -> tuple :
    Calcule les horaires de début des roulements et le nombre de cycles.

- init_dicts_comp(df_roulement_agent: pd.DataFrame) -> tuple :
    Génère les compétences des agents pour les différents chantiers.

- init_dicts(...) -> tuple :
    Regroupe et initialise l’ensemble des dictionnaires nécessaires à la modélisation.

- lightning_mcqueen_parser(file_path: str) -> tuple :
    Lit et analyse un fichier d'entrée pour en extraire les données nécessaires.

- ecriture_donnees_sortie(...) -> bool :
    Génère et écrit les résultats dans un fichier Excel.

Dépendances :
-------------
- pandas
- datetime
- itertools
- math
- autres modules spécifiques du projet (ex : Constantes, Colonnes)
"""

from datetime import datetime, timedelta
from itertools import chain
from math import ceil

import pandas as pd

from module.constants import Chantiers, Colonnes, Feuilles, Machines, Taches
from module.tools import (
    convert_hour_to_minutes,
    convertir_en_minutes,
    traitement_doublons,
)

# ----- dataframes ----- #


def init_dfs(file_path: str):
    """
    Charge plusieurs DataFrames à partir d'un fichier Excel et initialise
    certaines de ses données.

    Paramètres :
    ------------
    file_path : str
        Chemin du fichier Excel à charger.

    Retourne :
    ----------
    tuple
        Un tuple contenant les DataFrames suivants :
        - df : pd.DataFrame
            DataFrame brut lu depuis Excel.
        - df_sil_arr : pd.DataFrame
            Données des sillons d'arrivée.
        - df_sil_dep : pd.DataFrame
            Données des sillons de départ.
        - df_cor : pd.DataFrame
            Données des correspondances.
        - df_chantiers : pd.DataFrame
            Données des chantiers.
        - df_machines : pd.DataFrame
            Données des machines.
        - df_roulement_agent : pd.DataFrame
            Données du roulement des agents.
        - df_taches_humaines : pd.DataFrame
            Données des tâches humaines.
    """

    df = pd.read_excel(file_path, sheet_name=None)

    df_sil_arr = init_df_sillon_arr(df)
    df_sil_dep = init_df_sillon_dep(df)

    df_cor = init_df_correspondances(df)

    df_chantiers = df[Feuilles.CHANTIERS]
    df_machines = df[Feuilles.MACHINES]

    df_roulement_agent = df[Feuilles.ROULEMENT_AGENTS]
    df_taches_humaines = df[Feuilles.TACHES_HUMAINES]

    return (
        df,
        df_sil_arr,
        df_sil_dep,
        df_cor,
        df_chantiers,
        df_machines,
        df_roulement_agent,
        df_taches_humaines,
    )


def init_df_sillon_arr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des sillons d'arrivée en formatant les dates.

    Paramètres :
    ------------
    df : pd.DataFrame
        Dictionnaire contenant les DataFrames des feuilles Excel.

    Retourne :
    ----------
    pd.DataFrame
        Données des sillons d'arrivée avec les dates formatées.
    """

    df_sil_arr = df[Feuilles.SILLONS_ARRIVEE]
    df_sil_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sil_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_arr


def init_df_sillon_dep(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des sillons de départ en formatant les dates.

    Paramètres :
    ------------
    df : pd.DataFrame
        Dictionnaire contenant les DataFrames des feuilles Excel.

    Retourne :
    ----------
    pd.DataFrame
        Données des sillons de départ avec les dates formatées.
    """
    df_sil_dep = df[Feuilles.SILLONS_DEPART]
    df_sil_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sil_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_dep


def init_df_correspondances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des correspondances en générant des identifiants uniques.

    Paramètres :
    ------------
    df : pd.DataFrame
        Dictionnaire contenant les DataFrames des feuilles Excel.

    Retourne :
    ----------
    pd.DataFrame
        Données des correspondances avec les identifiants de trains générés.
    """
    input_df = df[Feuilles.CORRESPONDANCES].copy().astype(str)

    input_df[Colonnes.ID_TRAIN_ARRIVEE] = (
        input_df[Colonnes.N_TRAIN_ARRIVEE]
        + "_"
        + pd.to_datetime(
            input_df[Colonnes.DATE_ARRIVEE], format="%d/%m/%Y", errors="coerce"
        ).dt.strftime("%d")
    )

    input_df[Colonnes.ID_TRAIN_DEPART] = (
        input_df[Colonnes.N_TRAIN_DEPART]
        + "_"
        + pd.to_datetime(
            input_df[Colonnes.DATE_DEPART], format="%d/%m/%Y", errors="coerce"
        ).dt.strftime("%d")
    )

    return input_df


# ----- values ----- #


def skibidi_mondays(date: datetime) -> datetime:
    """
    Calcule le lundi de la semaine en cours pour une date donnée.

    Paramètres :
    ------------
    date : datetime
        Date pour laquelle trouver le lundi de la semaine.

    Retourne :
    ----------
    datetime
        Date correspondant au lundi de la semaine en cours.
    """
    jour_semaine = date.weekday()
    delta = timedelta(days=jour_semaine)
    return (date - delta).replace(hour=0, minute=0, microsecond=0)


def init_first_arr(df_sillons_arr: pd.DataFrame) -> datetime:
    """
    Calcule la première date et heure d'arrivée parmi les sillons.

    Paramètres :
    ------------
    df_sillons_arr : pd.DataFrame
        DataFrame contenant les sillons d'arrivée.

    Retourne :
    ----------
    datetime
        Date et heure de la première arrivée enregistrée.
    """
    df_sillons_arr["Datetime"] = pd.to_datetime(
        df_sillons_arr[Colonnes.SILLON_JARR].astype(str)
        + " "
        + df_sillons_arr[Colonnes.SILLON_HARR].astype(str)
    )
    return df_sillons_arr["Datetime"].min()


def init_last_dep(df_sillons_dep: pd.DataFrame) -> datetime:
    """
    Calcule la dernière date et heure de départ parmi les sillons.

    Paramètres :
    ------------
    df_sillons_dep : pd.DataFrame
        DataFrame contenant les sillons de départ.

    Retourne :
    ----------
    datetime
        Date et heure du dernier départ enregistré.
    """
    df_sillons_dep["Datetime"] = pd.to_datetime(
        df_sillons_dep[Colonnes.SILLON_JDEP].astype(str)
        + " "
        + df_sillons_dep[Colonnes.SILLON_HDEP].astype(str)
    )
    return df_sillons_dep["Datetime"].max()


def nombre_roulements(df_roulement_agent: pd.DataFrame) -> int:
    """
    Calcule le nombre total de roulements d'agents.

    Paramètres :
    ------------
    df_roulement_agent : pd.DataFrame
        DataFrame contenant les roulements d'agents.

    Retourne :
    ----------
    int
        Nombre total de roulements enregistrés.
    """
    count = df_roulement_agent[Colonnes.ROULEMENT].count()
    return count


def init_values(
    df_sillons_arr: pd.DataFrame,
    df_sillons_dep: pd.DataFrame,
    df_roulement_agent: pd.DataFrame,
) -> tuple[float, float, datetime, int]:
    """
    Initialise les valeurs temporelles et le nombre de roulements d'agents.

    Paramètres :
    ------------
    df_sillons_arr : pd.DataFrame
        DataFrame contenant les sillons d'arrivée.
    df_sillons_dep : pd.DataFrame
        DataFrame contenant les sillons de départ.
    df_roulement_agent : pd.DataFrame
        DataFrame contenant les roulements d'agents.

    Retourne :
    ----------
    tuple
        Un tuple contenant :
        - float : Temps écoulé en minutes jusqu'à la première arrivée.
        - float : Temps écoulé en minutes jusqu'au dernier départ.
        - datetime : Date du lundi de référence.
        - int : Nombre total de roulements d'agents.
    """
    first_arr = init_first_arr(df_sillons_arr)
    last_dep = init_last_dep(df_sillons_dep)

    monday = skibidi_mondays(first_arr)

    first_arr -= monday
    last_dep -= monday

    return (
        first_arr.total_seconds() / 60,
        last_dep.total_seconds() / 60,
        monday,
        nombre_roulements(df_roulement_agent),
    )


# ----- dicts ----- #


def init_dict_t_a(df_sillons_arr: pd.DataFrame, monday: datetime) -> dict:
    """
    Crée un dictionnaire des minutes écoulées depuis une date de référence pour
    chaque train d'arrivée.

    Cette fonction génère un dictionnaire où chaque clé est un identifiant unique
    de train (composé du numéro du train et de la date d'arrivée), et la valeur
    correspond aux minutes écoulées depuis la date de référence pour chaque train,
    jusqu'à son arrivée.

    Args:
        df_sillons_arr (pd.DataFrame): DataFrame contenant les données des sillons
                                      d'arrivée, incluant les informations sur les
                                      numéros de train, les dates et heures d'arrivée.
        monday (datetime): Date du lundi de référence.

    Returns:
        dict: Dictionnaire avec des identifiants uniques de trains comme clés et les
              minutes écoulées depuis la date de référence comme valeurs.
    """
    t_a = {}
    for _, row in df_sillons_arr.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_arr = row[Colonnes.SILLON_JARR]
        heure_arr = convert_hour_to_minutes(
            row[Colonnes.SILLON_HARR]
        )  # Conversion heure → minutes

        if pd.notna(date_arr) and heure_arr is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_arr - monday).days
            minutes_since_ref = (days_since_ref * 1440) + heure_arr  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date, car certains trains portant le même ID passent sur des jours différents
            train_id_unique = f"{train_id}_{date_arr.strftime('%d')}"

            t_a[train_id_unique] = minutes_since_ref
    return t_a


def init_dict_t_d(df_sillons_dep: pd.DataFrame, monday: datetime) -> dict:
    """
    Crée un dictionnaire des minutes écoulées depuis une date de référence pour
    chaque train de départ.

    Cette fonction génère un dictionnaire où chaque clé est un identifiant unique
    de train (composé du numéro du train et de la date de départ), et la valeur
    correspond aux minutes écoulées depuis la date de référence pour chaque train,
    jusqu'à  son départ.

    Args:
        df_sillons_dep (pd.DataFrame): DataFrame contenant les données des sillons
                                      de départ, incluant les informations sur les
                                      numéros de train, les dates et heures de départ.
        monday (datetime): Date du lundi de référence.

    Returns:
        dict: Dictionnaire avec des identifiants uniques de trains comme clés et les
              minutes écoulées depuis la date de référence comme valeurs.
    """
    t_d = {}
    for _, row in df_sillons_dep.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_dep = row[Colonnes.SILLON_JDEP]
        heure_dep = convert_hour_to_minutes(
            row[Colonnes.SILLON_HDEP]
        )  # Conversion heure → minutes

        if pd.notna(date_dep) and heure_dep is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_dep - monday).days
            minutes_since_ref = (days_since_ref * 1440) + heure_dep  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date
            train_id_unique = f"{train_id}_{date_dep.strftime('%d')}"

            t_d[train_id_unique] = minutes_since_ref
    return t_d


def init_dict_correspondances(df_correspondance: pd.DataFrame) -> dict:
    """
    Crée un dictionnaire des correspondances entre trains d'arrivée et de départ.

    Cette fonction génère un dictionnaire où chaque clé est un identifiant de train
    de départ et chaque valeur est une liste des identifiants des trains d'arrivée
    correspondants à ce train de départ.

    Args:
        df_correspondance (pd.DataFrame): DataFrame contenant les correspondances entre
                                          trains d'arrivée et de départ.

    Returns:
        dict: Dictionnaire où chaque clé est un identifiant de train de départ et chaque
              valeur est une liste d'identifiants de trains d'arrivée correspondants.
    """
    input_df = df_correspondance
    d = {}
    for departure_train_id in input_df[Colonnes.ID_TRAIN_DEPART]:
        d[departure_train_id] = []
    for arrival_train_id, departure_train_id in zip(
        input_df[Colonnes.ID_TRAIN_ARRIVEE],
        input_df[Colonnes.ID_TRAIN_DEPART],
    ):
        d[departure_train_id].append(arrival_train_id)
    return d


def init_dict_limites_chantiers(
    df_chantiers: pd.DataFrame,
    dernier_depart: float,
) -> dict:
    """
    Crée un dictionnaire des limites de disponibilité des chantiers en minutes.

    Cette fonction traite les indisponibilités des chantiers, les convertit en minutes
    et les organise dans un dictionnaire, où chaque clé correspond à un chantier
    spécifique et la valeur est la liste des limites de disponibilité.

    Args:
        df_chantiers (pd.DataFrame): DataFrame contenant les informations des chantiers,
                                     y compris les indisponibilités.
        dernier_depart (float): Heure du dernier départ en minutes depuis la référence.

    Returns:
        dict: Dictionnaire des limites de disponibilité des chantiers, avec des clés
              correspondant aux types de chantiers (REC, FOR, DEP) et des valeurs
              représentant les listes de limites de disponibilité.
    """
    indisponibilites_chantiers = df_chantiers[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_chantiers[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, dernier_depart))
    )
    listes_plates_chantiers = indisponibilites_chantiers.apply(
        lambda x: list(chain(*x))
    )

    limites_chantiers = []
    for liste in listes_plates_chantiers:
        limites_chantiers.append(liste)

    limites_chantiers = traitement_doublons(limites_chantiers)

    limites_chantiers_dict = {
        Chantiers.REC: limites_chantiers[0],
        Chantiers.FOR: limites_chantiers[1],
        Chantiers.DEP: limites_chantiers[2],
    }
    return limites_chantiers_dict


def init_dict_limites_machines(
    df_machines: pd.DataFrame,
    dernier_depart: float,
) -> dict:
    """
    Crée un dictionnaire des limites de disponibilité des machines en minutes.

    Cette fonction convertit les indisponibilités des machines en minutes et
    les organise dans un dictionnaire, où chaque clé correspond à un type
    de machine et la valeur est la liste des limites de disponibilité.

    Args:
        df_machines (pd.DataFrame): DataFrame contenant les informations des
                                    machines, y compris les indisponibilités.
        dernier_depart (float): Heure du dernier départ en minutes depuis
                                la référence.

    Returns:
        dict: Dictionnaire des limites de disponibilité des machines, avec des
              clés correspondant aux types de machines (DEB, FOR, DEG) et des
              valeurs représentant les listes de limites de disponibilité.
    """
    indisponibilites_machines = df_machines[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_machines[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, dernier_depart))
    )

    listes_plates_machines = indisponibilites_machines.apply(lambda x: list(chain(*x)))

    limites_machines = []
    for liste in listes_plates_machines:
        limites_machines.append(liste)

    limites_machines = traitement_doublons(limites_machines)
    limites_machines = {
        Machines.DEB: limites_machines[0],
        Machines.FOR: limites_machines[1],
        Machines.DEG: limites_machines[2],
    }

    return limites_machines


def init_dict_limites_voies(df_chantiers: pd.DataFrame) -> dict:
    """
    Crée un dictionnaire des limites de voies disponibles pour chaque chantier.

    Cette fonction extrait le nombre de voies disponibles pour chaque chantier
    et les stocke dans un dictionnaire où chaque clé représente un type de
    chantier et la valeur correspondante est le nombre de voies disponibles.

    Args:
        df_chantiers (pd.DataFrame): DataFrame contenant les informations sur
                                     les chantiers, y compris le nombre de voies.

    Returns:
        dict: Dictionnaire avec les types de chantiers (REC, FOR, DEP) comme
              clés et le nombre de voies disponibles comme valeurs.
    """
    limites_chantiers_voies = {
        Chantiers.REC: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[0]),
        Chantiers.FOR: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[1]),
        Chantiers.DEP: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[2]),
    }
    return limites_chantiers_voies


def init_dict_nombre_max_agents_sur_roulement(
    df_roulement_agent: pd.DataFrame,
) -> dict:
    """
    Crée un dictionnaire du nombre maximal d'agents par roulement.

    Cette fonction extrait le nombre d'agents associés à chaque roulement et
    les stocke dans un dictionnaire où chaque clé représente un roulement et
    la valeur correspondante est le nombre maximal d'agents.

    Args:
        df_roulement_agent (pd.DataFrame): DataFrame contenant les informations
                                           sur les roulements des agents.

    Returns:
        dict: Dictionnaire avec les numéros de roulement comme clés et le
              nombre maximal d'agents comme valeurs.
    """
    n_agent = {
        r + 1: df_roulement_agent.at[r, Colonnes.NOMBRE_AGENTS]
        for r in df_roulement_agent.index
    }

    return n_agent


def init_dict_roulements_operants_sur_tache(
    df_roulement_agent: pd.DataFrame,
) -> dict:
    """
    Crée un dictionnaire des roulements d'agents opérant sur chaque tâche.

    Cette fonction identifie les roulements d'agents ayant les connaissances
    nécessaires pour travailler sur différents chantiers et les organise dans
    un dictionnaire.

    Args:
        df_roulement_agent (pd.DataFrame): DataFrame contenant les roulements
                                           des agents et leurs compétences.

    Returns:
        dict: Dictionnaire où les clés sont des tuples (tâche, machine) et les
              valeurs sont des listes de roulements pouvant opérer sur ces tâches.
    """
    roulements_operants_sur_m = {}
    for m in [1, 2, 3]:
        roulements_operants_sur_m[("arr", m)] = (
            df_roulement_agent[
                df_roulement_agent[Colonnes.CONNAISSANCES_CHANTIERS].str.contains(
                    "REC", na=False
                )
            ].index
            + 1
        ).tolist()
        roulements_operants_sur_m[("dep", m)] = (
            df_roulement_agent[
                df_roulement_agent[Colonnes.CONNAISSANCES_CHANTIERS].str.contains(
                    "FOR", na=False
                )
            ].index
            + 1
        ).tolist()
    for m in [4]:
        roulements_operants_sur_m[("dep", m)] = (
            df_roulement_agent[
                df_roulement_agent[Colonnes.CONNAISSANCES_CHANTIERS].str.contains(
                    "DEP", na=False
                )
            ].index
            + 1
        ).tolist()
    return roulements_operants_sur_m


def init_dicts_heure_debut_roulement(
    df_roulement_agent: pd.DataFrame, first_arr: int, last_dep: int, monday: datetime
) -> tuple[
    dict,
    dict,
    dict,
]:
    """
    Initialise les dictionnaires des heures de début des roulements.

    Cette fonction crée plusieurs dictionnaires permettant de gérer les
    horaires des agents en fonction de leur disponibilité et des cycles
    horaires définis.

    Args:
        df_roulement_agent (pd.DataFrame): DataFrame contenant les informations
                                           sur les roulements des agents.
        first_arr (int): Heure d'arrivée du premier train en minutes.
        last_dep (int): Heure de départ du dernier train en minutes.
        monday (datetime): Date du lundi de référence.

    Returns:
        tuple:
            - dict h_deb: Heure de début des cycles par roulement et index.
            - dict nb_cycles_agents: Nombre total de cycles par agent.
            - dict nb_cycle_jour: Nombre de cycles quotidiens par agent.
    """
    nb_roulements = df_roulement_agent.shape[0]

    delta = last_dep - first_arr
    delta_jours = ceil(delta / (60 * 24))

    jour_semaine_disponibilite = {
        i + 1: [int(x) for x in str(row).split(";")]
        for i, row in enumerate(df_roulement_agent["Jours de la semaine"].dropna())
    }

    h_deb_jour = {
        i + 1: sorted(
            [
                timedelta(hours=int(x[:2]), minutes=int(x[3:5]))
                for x in str(row).split(";")
            ]
        )
        for i, row in enumerate(df_roulement_agent["Cycles horaires"].dropna())
    }

    nb_cycle_jour = {r: len(h_deb_jour[r]) for r in h_deb_jour}

    jour_de_la_semaine = monday
    dernier_jour_de_la_semaine = jour_de_la_semaine + timedelta(days=delta_jours)

    h_deb0 = {i + 1: [] for i in range(nb_roulements)}

    while jour_de_la_semaine <= dernier_jour_de_la_semaine:
        for r in range(1, nb_roulements + 1):
            if (jour_de_la_semaine.weekday()) % 7 + 1 in jour_semaine_disponibilite[r]:
                h_deb0[r] += [jour_de_la_semaine + t for t in h_deb_jour[r]]
        jour_de_la_semaine += timedelta(days=1)

    nb_cycles_agents = {r: len(h_deb0[r]) for r in h_deb0}

    h_deb = {
        (r, k + 1): int((h_deb0[r][k] - monday).total_seconds() / 60)
        for r in range(1, nb_roulements + 1)
        for k in range(nb_cycles_agents[r])
    }

    return h_deb, nb_cycles_agents, nb_cycle_jour


def init_dicts_comp(df_roulement_agent: pd.DataFrame) -> tuple[dict, dict]:
    """
    Initialise les dictionnaires des compétences des agents par roulement.

    Cette fonction analyse les connaissances des agents sur les chantiers et
    les classe en deux catégories : compétences pour l'arrivée et pour le départ.

    Args:
        df_roulement_agent (pd.DataFrame): DataFrame contenant les roulements
                                           et compétences des agents.

    Returns:
        tuple:
            - dict comp_arr: Dictionnaire des compétences des agents pour
              l'arrivée, avec les roulements comme clés et les tâches associées
              comme valeurs.
            - dict comp_dep: Dictionnaire des compétences des agents pour
              le départ, structuré de la même manière.
    """
    comp_arr = {}
    comp_dep = {}

    for r in range(1, len(df_roulement_agent) + 1):
        comp_arr[r] = []
        comp_dep[r] = []
        value = str(df_roulement_agent.loc[r - 1, "Connaissances chantiers"])
        if "WPY_REC" in value:
            comp_arr[r] += [1, 2, 3]
        if "WPY_FOR" in value:
            comp_dep[r] += [1, 2, 3]
        if "WPY_DEP" in value:
            comp_dep[r] += [4]

    return comp_arr, comp_dep


def init_dicts(
    df_sillons_arr: pd.DataFrame,
    df_sillons_dep: pd.DataFrame,
    df_correspondance: pd.DataFrame,
    df_chantiers: pd.DataFrame,
    df_machines: pd.DataFrame,
    df_roulement_agent: pd.DataFrame,
    first_arr: float,
    dernier_depart: float,
    monday: datetime,
) -> tuple[
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
]:
    """
    Initialise et retourne plusieurs dictionnaires utiles pour la gestion
    des sillons, chantiers, machines et roulements d'agents.

    Args:
        df_sillons_arr (pd.DataFrame): Données des sillons d'arrivée.
        df_sillons_dep (pd.DataFrame): Données des sillons de départ.
        df_correspondance (pd.DataFrame): Données des correspondances.
        df_chantiers (pd.DataFrame): Données des chantiers.
        df_machines (pd.DataFrame): Données des machines.
        df_roulement_agent (pd.DataFrame): Données des roulements d'agents.
        first_arr (float): Heure du premier train en minutes.
        dernier_depart (float): Heure du dernier départ en minutes.
        monday (datetime): Date du lundi de référence.

    Returns:
        tuple:
            - dict t_a: Heures d'arrivée des trains.
            - dict t_d: Heures de départ des trains.
            - dict correspondances: Correspondances entre trains.
            - dict limites_chantiers: Indisponibilités des chantiers.
            - dict limites_machines: Indisponibilités des machines.
            - dict limites_voies: Nombre de voies disponibles.
            - dict max_agents: Nombre max d'agents par roulement.
            - dict roulements_taches: Roulements opérants sur tâches.
            - dict h_deb: Heures de début des cycles d'agents.
            - dict nb_cycles_agents: Nombre total de cycles par agent.
            - dict nb_cycle_jour: Nombre de cycles quotidiens par agent.
            - dict comp_arr: Compétences agents pour l'arrivée.
            - dict comp_dep: Compétences agents pour le départ.
    """
    h_deb, nb_cycles_agents, nb_cycle_jour = init_dicts_heure_debut_roulement(
        df_roulement_agent, first_arr, dernier_depart, monday
    )
    comp_arr, comp_dep = init_dicts_comp(df_roulement_agent)
    return (
        init_dict_t_a(df_sillons_arr, monday),
        init_dict_t_d(df_sillons_dep, monday),
        init_dict_correspondances(df_correspondance),
        init_dict_limites_chantiers(
            df_chantiers,
            dernier_depart,
        ),
        init_dict_limites_machines(
            df_machines,
            dernier_depart,
        ),
        init_dict_limites_voies(df_chantiers),
        init_dict_nombre_max_agents_sur_roulement(df_roulement_agent),
        init_dict_roulements_operants_sur_tache(df_roulement_agent),
        h_deb,
        nb_cycles_agents,
        nb_cycle_jour,
        comp_arr,
        comp_dep,
    )


# ----- parser -----#


def lightning_mcqueen_parser(file_path: str):
    """
    Parse le fichier source et initialise les données nécessaires à l'analyse.

    Args:
        file_path (str): Chemin du fichier contenant les données.

    Returns:
        tuple: Contient les valeurs suivantes :
            - first_arr (float): Heure du premier train en minutes.
            - dernier_depart (float): Heure du dernier départ en minutes.
            - monday (datetime): Date du lundi de référence.
            - nb_roulements (int): Nombre total de roulements.
            - df_sillons_arr (pd.DataFrame): Données des sillons d'arrivée.
            - df_sillons_dep (pd.DataFrame): Données des sillons de départ.
            - df_correspondance (pd.DataFrame): Données des correspondances.
            - df_chantiers (pd.DataFrame): Données des chantiers.
            - df_machines (pd.DataFrame): Données des machines.
            - df_roulement_agent (pd.DataFrame): Données des roulements d'agents.
            - df_taches_humaines (pd.DataFrame): Données des tâches humaines.
            - dict_t_a (dict): Heures d'arrivée des trains.
            - dict_t_d (dict): Heures de départ des trains.
            - dict_correspondances (dict): Correspondances entre trains.
            - dict_limites_chantiers (dict): Indisponibilités des chantiers.
            - dict_limites_machines (dict): Indisponibilités des machines.
            - dict_limites_voies (dict): Nombre de voies disponibles.
            - dict_max_agents (dict): Nombre max d'agents par roulement.
            - dict_roulements_operants_sur_tache (dict): Roulements par tâche.
            - dict_h_deb (dict): Heures de début des cycles d'agents.
            - dict_nb_cycles_agents (dict): Nombre total de cycles par agent.
            - dict_nb_cycle_jour (dict): Nombre de cycles quotidiens par agent.
            - dict_comp_arr (dict): Compétences agents pour l'arrivée.
            - dict_comp_dep (dict): Compétences agents pour le départ.
    """
    (
        _,
        df_sillons_arr,
        df_sillons_dep,
        df_correspondance,
        df_chantiers,
        df_machines,
        df_roulement_agent,
        df_taches_humaines,
    ) = init_dfs(file_path)

    first_arr, dernier_depart, monday, nb_roulements = init_values(
        df_sillons_arr, df_sillons_dep, df_roulement_agent
    )
    (
        dict_t_a,
        dict_t_d,
        dict_correspondances,
        dict_limites_chantiers,
        dict_limites_machines,
        dict_limites_voies,
        dict_max_agents,
        dict_roulements_operants_sur_tache,
        dict_h_deb,
        dict_nb_cycles_agents,
        dict_nb_cycle_jour,
        dict_comp_arr,
        dict_comp_dep,
    ) = init_dicts(
        df_sillons_arr,
        df_sillons_dep,
        df_correspondance,
        df_chantiers,
        df_machines,
        df_roulement_agent,
        first_arr,
        dernier_depart,
        monday,
    )

    return (
        first_arr,
        dernier_depart,
        monday,
        nb_roulements,
        #
        df_sillons_arr,
        df_sillons_dep,
        df_correspondance,
        df_chantiers,
        df_machines,
        df_roulement_agent,
        df_taches_humaines,
        #
        dict_t_a,
        dict_t_d,
        dict_correspondances,
        dict_limites_chantiers,
        dict_limites_machines,
        dict_limites_voies,
        dict_max_agents,
        dict_roulements_operants_sur_tache,
        dict_h_deb,
        dict_nb_cycles_agents,
        dict_nb_cycle_jour,
        dict_comp_arr,
        dict_comp_dep,
    )


# ----- writting files -----#


def ecriture_donnees_sortie(
    t_arr: dict,
    t_dep: dict,
    occupation_REC: list,
    occupation_FOR: list,
    occupation_DEP: list,
    x_date: list,
    limites_voies: dict,
    h_deb: dict,
    equip: dict,
    nb_cycles_agents: dict,
    who_arr: dict,
    who_dep: dict,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    nombre_agents: dict,
    nb_cycle_jour: dict,
    df_roulement_agent: pd.DataFrame,
    df_taches_humaines: pd.DataFrame,
    file_name: str,
    monday: datetime,
):
    """
    Traite les données pour les mettre dans une feuille de calcul de sortie au format standard.

    Paramètres :
    -----------
    t_arr : dict
        Variables de début des tâches d'arrivée.
    t_dep: dict
        Variables de début des tâches de départ.
    occupation_REC : list
        Occupation des voies du chantier de réception en fonction du temps.
    occupation_REC : list
        Occupation des voies du chantier de formation en fonction du temps.
    occupation_DEP : list
        Occupation des voies du chantier de départ en fonction du temps.
    x_date : list
        Horodatage des points des listes précédentes.
    limites_voies : dict
        Nombre de voies utilisables par chantier.
    h_deb : dict
        Horaires de début des cycles des agents.
    equip : dict
        Compétences des équipes pour chaque tâche.
    nb_cycles_agents : dict
        Nombre de cycles pour chaque roulement.
    who_arr : dict
        Variables indiquant si une tâche d'arrivée est assignée à un agent.
    who_dep : dict
        Variables indiquant si une tâche de départ est assignée à un agent.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    nombre_agents : dict
        Nombre d'agents du roulement activés pour le cycle.
    nb_cycle_jour :
        Nombre de cycle par jour du roulement.
    df_roulement_agent : pd.DataFrame
        DataFrame contenant les informations sur les roulements des agents.
    df_taches_humaines : pd.DataFrame
        DataFrame contenant les informations sur les taches des agents.
    file_name : str
        Nom du fichier de sortie (sans l'extension)
    monday : datetime
        Date du lundi de référence.

    Retourne :
    ---------
    bool
        True si les données sont écrites.
    """
    # Création des données de sortie
    xl = (
        [
            {
                "Id tâche": "DEB_"
                + n_arr
                + "#"
                + (monday + timedelta(minutes=15 * var_arr)).strftime("%d/%m/%Y")
                + "#A",
                "Type de tâche": "DEB",
                "Jour": (monday + timedelta(minutes=15 * var_arr)).strftime("%d/%m/%Y"),
                "Heure de début": (monday + timedelta(minutes=15 * var_arr)).strftime(
                    "%H:%M"
                ),
                "Durée": Taches.T_ARR[m_arr],
                "Sillon": n_arr
                + "#"
                + (monday + timedelta(minutes=15 * var_arr)).strftime("%d/%m/%Y")
                + "#A",
            }
            for (m_arr, n_arr), var_arr in t_arr.items()
            if m_arr == 3
        ]
        + [
            {
                "Id tâche": "FOR_"
                + n_dep
                + "#"
                + (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y")
                + "#D",
                "Type de tâche": "FOR",
                "Jour": (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y"),
                "Heure de début": (monday + timedelta(minutes=15 * var_dep)).strftime(
                    "%H:%M"
                ),
                "Durée": Taches.T_DEP[m_dep],
                "Sillon": n_dep
                + "#"
                + (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y")
                + "#D",
            }
            for (m_dep, n_dep), var_dep in t_dep.items()
            if m_dep == 1
        ]
        + [
            {
                "Id tâche": "DEG_"
                + n_dep
                + "#"
                + (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y")
                + "#D",
                "Type de tâche": "DEG",
                "Jour": (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y"),
                "Heure de début": (monday + timedelta(minutes=15 * var_dep)).strftime(
                    "%H:%M"
                ),
                "Durée": Taches.T_DEP[m_dep],
                "Sillon": n_dep
                + "#"
                + (monday + timedelta(minutes=15 * var_dep)).strftime("%d/%m/%Y")
                + "#D",
            }
            for (m_dep, n_dep), var_dep in t_dep.items()
            if m_dep == 3
        ]
    )

    # Versement des données de sortie vers une trame de données
    df_xl = pd.DataFrame(xl)

    # Création des données d'occupation des voies de chantier
    xl2 = {
        "Horodatage": x_date,
        "REC": occupation_REC,
        "FOR": occupation_FOR,
        "DEP": occupation_DEP,
    }
    # Versement des données d'occupation vers une trame de données
    df_xl2 = pd.DataFrame(xl2)

    xl3 = {
        "Occupation des voies par chantier (optim)": [
            "Taux max d'occupation des voies (en %)",
            "Nombre max de voies occupées",
            "Nombre total de voies à disposition",
        ],
        "WPY_REC": [
            100 * max(occupation_REC) / limites_voies[Chantiers.REC],
            max(occupation_REC),
            limites_voies[Chantiers.REC],
        ],
        "WPY_FOR": [
            100 * max(occupation_FOR) / limites_voies[Chantiers.FOR],
            max(occupation_FOR),
            limites_voies[Chantiers.FOR],
        ],
        "WPY_DEP": [
            100 * max(occupation_DEP) / limites_voies[Chantiers.DEP],
            max(occupation_DEP),
            limites_voies[Chantiers.DEP],
        ],
    }

    df_xl3 = pd.DataFrame(xl3)

    df_xl4, df_xl5 = ecriture_donnees_sortie_jalon3(
        t_arr,
        t_dep,
        h_deb,
        equip,
        nb_cycles_agents,
        who_arr,
        who_dep,
        liste_id_train_arrivee,
        liste_id_train_depart,
        nombre_agents,
        nb_cycle_jour,
        nb_cycles_agents,
        df_roulement_agent,
        df_taches_humaines,
        monday,
    )

    # Versement des trames vers la feuilles de calcul
    with pd.ExcelWriter(f"{file_name}.xlsx", engine="openpyxl") as writer:
        df_xl.to_excel(writer, sheet_name="Taches machine", index=False)
        df_xl2.to_excel(writer, sheet_name="Occupation voie chantier", index=False)
        df_xl3.to_excel(
            writer, sheet_name="Statistiques occupation voie chantier", index=False
        )
        df_xl4.to_excel(writer, sheet_name="Roulements agents", index=False)
        df_xl5.to_excel(writer, sheet_name="Statistiques roulements", index=False)

    return True


def ecriture_donnees_sortie_jalon3(
    t_arr: dict,
    t_dep: dict,
    h_deb: dict,
    equip: dict,
    nb_cycles_agents: dict,
    who_arr: dict,
    who_dep: dict,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    nombre_agents: dict,
    nb_cycle_jour: int,
    nombre_cycles_agents: int,
    df_roulement_agent: pd.DataFrame,
    df_taches_humaines: pd.DataFrame,
    monday: datetime,
) -> bool:
    """
    Formate et écrit les données traitées dans une feuille de calcul de sortie.

    Paramètres :
    ------------
    t_arr : dict
        Variables de début des tâches d'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    h_deb : dict
        Horaires de début des cycles des agents.
    equip : dict
        Équipement des agents pour chaque tâche.
    nb_cycles_agents : dict
        Nombre de cycles pour chaque roulement d'agent.
    who_arr : dict
        Indicateurs d'affectation des tâches d'arrivée aux agents.
    who_dep : dict
        Indicateurs d'affectation des tâches de départ aux agents.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    nombre_agents : dict
        Nombre d'agents actifs pour chaque roulement et cycle.
    nb_cycle_jour : int
        Nombre de cycles par jour pour un roulement.
    nombre_cycles_agents : int
        Nombre total de cycles par roulement.
    df_roulement_agent : pd.DataFrame
        Informations sur les roulements des agents.
    df_taches_humaines : pd.DataFrame
        Informations sur les tâches effectuées par les agents.
    monday : datetime
        Date du lundi de référence.

    Retourne :
    ----------
    bool
        True si les données sont correctement écrites.
    """
    noms_roulements = {
        r + 1: df_roulement_agent.at[r, "Roulement"] for r in df_roulement_agent.index
    }
    noms_tache = {
        m + 1: df_taches_humaines.at[m, "Type de tache humaine"]
        for m in df_taches_humaines.index
    }

    def get_time_string(var) -> str:
        """
        Convertit une variable Gurobi en chaîne de date et heure formatée.

        Paramètres :
        ------------
        var : grb.Var | int
            Variable Gurobi ou entier représentant un temps en intervalles.

        Retourne :
        ----------
        str
            Chaîne de caractères représentant la date et l'heure formatées.
        """
        var_value = int(var.X) if hasattr(var, "X") else int(var)
        return (monday + timedelta(minutes=15 * var_value)).strftime("%d/%m/%Y %H:%M")

    xl = (
        [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_arr[1, n_arr]),
                "Ordre T": 1,
                "Type T": noms_tache[1],
                "Sillon": f"{n_arr}#{get_time_string(t_arr[1, n_arr])}#A",
                "Début T": get_time_string(t_arr[1, n_arr]),
                "Durée T": Taches.T_ARR[1],
                "Lieu T": "WPY_REC",
                "Roulement": noms_roulements[r],
            }
            for n_arr in liste_id_train_arrivee
            for r in equip[("arr", 1)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_arr[1, n_arr] >= h_deb[r, k]
            and 15 * t_arr[1, n_arr] + Taches.T_ARR[1] <= h_deb[r, k] + 8 * 60
            if who_arr[(1, n_arr, r, k, 3 * t_arr[1, n_arr])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_arr[2, n_arr]),
                "Ordre T": 2,
                "Type T": noms_tache[2],
                "Sillon": f"{n_arr}#{get_time_string(t_arr[2, n_arr])}#A",
                "Début T": get_time_string(t_arr[2, n_arr]),
                "Durée T": Taches.T_ARR[2],
                "Lieu T": "WPY_REC",
                "Roulement": noms_roulements[r],
            }
            for n_arr in liste_id_train_arrivee
            for r in equip[("arr", 2)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_arr[2, n_arr] >= h_deb[r, k]
            and 15 * t_arr[2, n_arr] + Taches.T_ARR[2] <= h_deb[r, k] + 8 * 60
            if who_arr[(2, n_arr, r, k, 3 * t_arr[2, n_arr])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_arr[3, n_arr]),
                "Ordre T": 3,
                "Type T": noms_tache[3],
                "Sillon": f"{n_arr}#{get_time_string(t_arr[3, n_arr])}#A",
                "Début T": get_time_string(t_arr[3, n_arr]),
                "Durée T": Taches.T_ARR[3],
                "Lieu T": "WPY_REC",
                "Roulement": noms_roulements[r],
            }
            for n_arr in liste_id_train_arrivee
            for r in equip[("arr", 3)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_arr[3, n_arr] >= h_deb[r, k]
            and 15 * t_arr[3, n_arr] + Taches.T_ARR[3] <= h_deb[r, k] + 8 * 60
            if who_arr[(3, n_arr, r, k, 3 * t_arr[3, n_arr])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_dep[3, n_dep]),
                "Ordre T": 1,
                "Type T": noms_tache[4],
                "Sillon": f"{n_dep}#{get_time_string(t_dep[3, n_dep])}#A",
                "Début T": get_time_string(t_dep[3, n_dep]),
                "Durée T": Taches.T_DEP[1],
                "Lieu T": "WPY_FOR",
                "Roulement": noms_roulements[r],
            }
            for n_dep in liste_id_train_depart
            for r in equip[("dep", 1)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_dep[1, n_dep] >= h_deb[r, k]
            and 15 * t_dep[1, n_dep] + Taches.T_DEP[1] <= h_deb[r, k] + 8 * 60
            if who_dep[(1, n_dep, r, k, 3 * t_dep[1, n_dep])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_dep[2, n_dep]),
                "Ordre T": 2,
                "Type T": noms_tache[5],
                "Sillon": f"{n_dep}#{get_time_string(t_dep[2, n_dep])}#A",
                "Début T": get_time_string(t_dep[2, n_dep]),
                "Durée T": Taches.T_DEP[2],
                "Lieu T": "WPY_FOR",
                "Roulement": noms_roulements[r],
            }
            for n_dep in liste_id_train_depart
            for r in equip[("dep", 2)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_dep[2, n_dep] >= h_deb[r, k]
            and 15 * t_dep[2, n_dep] + Taches.T_DEP[2] <= h_deb[r, k] + 8 * 60
            if who_dep[(2, n_dep, r, k, 3 * t_dep[2, n_dep])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_dep[3, n_dep]),
                "Ordre T": 3,
                "Type T": noms_tache[6],
                "Sillon": f"{n_dep}#{get_time_string(t_dep[3, n_dep])}#A",
                "Début T": get_time_string(t_dep[3, n_dep]),
                "Durée T": Taches.T_DEP[3],
                "Lieu T": "WPY_FOR",
                "Roulement": noms_roulements[r],
            }
            for n_dep in liste_id_train_depart
            for r in equip[("dep", 3)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_dep[3, n_dep] >= h_deb[r, k]
            and 15 * t_dep[3, n_dep] + Taches.T_DEP[3] <= h_deb[r, k] + 8 * 60
            if who_dep[(3, n_dep, r, k, 3 * t_dep[3, n_dep])].X == 1
        ]
        + [
            {
                "Id JS": noms_roulements[r]
                + "_"
                + str((h_deb[(r, k)] % 1440) // 60)
                + "_"
                + get_time_string(t_dep[4, n_dep]),
                "Ordre T": 4,
                "Type T": noms_tache[7],
                "Sillon": f"{n_dep}#{get_time_string(t_dep[4, n_dep])}#A",
                "Début T": get_time_string(t_dep[4, n_dep]),
                "Durée T": Taches.T_DEP[4],
                "Lieu T": "WPY_DEP",
                "Roulement": noms_roulements[r],
            }
            for n_dep in liste_id_train_depart
            for r in equip[("dep", 4)]
            for k in range(1, nb_cycles_agents[r] + 1)
            if 15 * t_dep[4, n_dep] >= h_deb[r, k]
            and 15 * t_dep[4, n_dep] + Taches.T_DEP[4] <= h_deb[r, k] + 8 * 60
            if who_dep[(4, n_dep, r, k, 3 * t_dep[4, n_dep])].X == 1
        ]
    )

    df_xl = pd.DataFrame(xl)

    xl2 = {"Nb de JS activées": [noms_roulements[r] for r in noms_roulements.keys()]}

    nb_jour = nombre_cycles_agents[1] // nb_cycle_jour[1]

    for j in range(nb_jour):
        xl2[(monday + timedelta(days=j)).strftime(format="%d/%m/%Y")] = [
            0 for r in noms_roulements.keys()
        ]
    for r in noms_roulements.keys():
        for k in range(1, nombre_cycles_agents[r] + 1):
            xl2[(monday + timedelta(minutes=h_deb[r, k])).strftime(format="%d/%m/%Y")][
                r - 1
            ] += nombre_agents[r, k].X

    xl2["Total"] = [
        sum(
            [
                xl2[(monday + timedelta(days=j)).strftime(format="%d/%m/%Y")][r - 1]
                for j in range(nb_jour)
            ]
        )
        for r in noms_roulements.keys()
    ]

    df_xl2 = pd.DataFrame(xl2)

    return df_xl, df_xl2
