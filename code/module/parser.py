"""to parse mf excels"""

import pandas as pd
from datetime import datetime, timedelta
from itertools import chain
from math import ceil
from module.constants import (
    Constantes,
    Machines,
    Chantiers,
    Feuilles,
    Colonnes,
)
from module.tools import (
    convert_hour_to_minutes,
    convertir_en_minutes,
    traitement_doublons,
)

# ----- dataframes ----- #


def init_dfs(file_path: str):
    """
    Initialise et charge plusieurs DataFrames à partir d'un fichier Excel.

    Cette fonction lit un fichier Excel contenant plusieurs feuilles et extrait
    les données sous forme de DataFrames spécifiques pour les sillons d'arrivée,
    les sillons de départ, les correspondances, les chantiers, les machines et
    le roulement des agents.

    Args:
        file_path (str): Chemin du fichier Excel à charger.

    Returns:
        tuple: Un tuple contenant les DataFrames suivants :
            - df (dict): Dictionnaire des DataFrames bruts lus depuis Excel.
            - df_sil_arr (DataFrame): Données des sillons d'arrivée.
            - df_sil_dep (DataFrame): Données des sillons de départ.
            - df_cor (DataFrame): Données des correspondances.
            - df_chantiers (DataFrame): Données des chantiers.
            - df_machines (DataFrame): Données des machines.
            - df_roulement_agent (DataFrame): Données du roulement des agents.
    """
    df = pd.read_excel(file_path, sheet_name=None)

    df_sil_arr = init_df_sillon_arr(df)
    df_sil_dep = init_df_sillon_dep(df)

    df_cor = init_df_correspondances(df)

    df_chantiers = df[Feuilles.CHANTIERS]
    df_machines = df[Feuilles.MACHINES]

    df_roulement_agent = df[Feuilles.ROULEMENT_AGENTS]

    return (
        df,
        df_sil_arr,
        df_sil_dep,
        df_cor,
        df_chantiers,
        df_machines,
        df_roulement_agent,
    )


def init_df_sillon_arr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des sillons d'arrivée en convertissant les dates.

    Cette fonction extrait la feuille correspondant aux sillons d'arrivée et
    convertit la colonne des dates en format datetime.

    Args:
        df (pd.DataFrame): Dictionnaire contenant les DataFrames des feuilles Excel.

    Returns:
        pd.DataFrame: DataFrame des sillons d'arrivée avec les dates formatées.
    """

    df_sil_arr = df[Feuilles.SILLONS_ARRIVEE]
    df_sil_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sil_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_arr


def init_df_sillon_dep(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des sillons de départ en convertissant les dates.

    Cette fonction extrait la feuille correspondant aux sillons de départ et
    convertit la colonne des dates en format datetime.

    Args:
        df (pd.DataFrame): Dictionnaire contenant les DataFrames des feuilles Excel.

    Returns:
        pd.DataFrame: DataFrame des sillons de départ avec les dates formatées.
    """
    df_sil_dep = df[Feuilles.SILLONS_DEPART]
    df_sil_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sil_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_dep


def init_df_correspondances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialise le DataFrame des correspondances en générant des identifiants uniques.

    Cette fonction extrait la feuille des correspondances, la convertit en chaîne
    de caractères et crée des identifiants uniques pour les trains d'arrivée et
    de départ en combinant leur numéro avec le jour du mois de leur date.

    Args:
        df (pd.DataFrame): Dictionnaire contenant les DataFrames des feuilles Excel.

    Returns:
        pd.DataFrame: DataFrame des correspondances avec les identifiants de trains générés.
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

    Cette fonction détermine le lundi de la semaine correspondant à la date
    fournie en soustrayant le nombre de jours écoulés depuis le dernier lundi.

    Args:
        date (datetime): Date pour laquelle trouver le lundi de la semaine.

    Returns:
        datetime: Date correspondant au lundi de la même semaine.
    """
    jour_semaine = date.weekday()
    delta = timedelta(days=jour_semaine)
    return date - delta


def init_first_arr(df_sillons_arr: pd.DataFrame) -> datetime:
    """
    Calcule la première date et heure d'arrivée parmi les sillons.

    Cette fonction fusionne les colonnes de date et d'heure d'arrivée en une seule
    colonne datetime, puis retourne la date et l'heure minimales.

    Args:
        df_sillons_arr (pd.DataFrame): DataFrame contenant les sillons d'arrivée.

    Returns:
        datetime: Date et heure de la première arrivée enregistrée.
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

    Cette fonction fusionne les colonnes de date et d'heure de départ en une seule
    colonne datetime, puis retourne la date et l'heure maximales.

    Args:
        df_sillons_dep (pd.DataFrame): DataFrame contenant les sillons de départ.

    Returns:
        datetime: Date et heure du dernier départ enregistré.
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

    Cette fonction compte le nombre de valeurs non nulles dans la colonne des
    roulements d'agents.

    Args:
        df_roulement_agent (pd.DataFrame): DataFrame contenant les roulements d'agents.

    Returns:
        int: Nombre total de roulements enregistrés.
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

    Cette fonction calcule le temps écoulé en minutes entre le début de la semaine
    (lundi à 00:00) et la première arrivée ainsi que le dernier départ.
    Elle retourne également la date du lundi de référence et le nombre de roulements.

    Args:
        df_sillons_arr (pd.DataFrame): DataFrame des sillons d'arrivée.
        df_sillons_dep (pd.DataFrame): DataFrame des sillons de départ.
        df_roulement_agent (pd.DataFrame): DataFrame des roulements d'agents.

    Returns:
        tuple[float, float, datetime, int]:
            - Temps écoulé en minutes jusqu'à la première arrivée.
            - Temps écoulé en minutes jusqu'au dernier départ.
            - Date du lundi de référence.
            - Nombre total de roulements d'agents.
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


def init_dict_t_a(df_sillons_arr: pd.DataFrame) -> dict:
    """
    Crée un dictionnaire des minutes écoulées depuis une date de référence pour
    chaque train d'arrivée.

    Cette fonction génère un dictionnaire où chaque clé est un identifiant unique
    de train (composé du numéro du train et de la date d'arrivée), et la valeur
    correspond aux minutes écoulées depuis la date de référence pour chaque train.

    Args:
        df_sillons_arr (pd.DataFrame): DataFrame contenant les données des sillons
                                      d'arrivée, incluant les informations sur les
                                      numéros de train, les dates et heures d'arrivée.

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
            days_since_ref = (date_arr - Constantes.BASE_TIME).days
            minutes_since_ref = (days_since_ref * 1440) + heure_arr  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date, car certains trains portant le même ID passent sur des jours différents
            train_id_unique = f"{train_id}_{date_arr.strftime('%d')}"

            t_a[train_id_unique] = minutes_since_ref
    return t_a


def init_dict_t_d(df_sillons_dep: pd.DataFrame) -> dict:
    """
    Crée un dictionnaire des minutes écoulées depuis une date de référence pour
    chaque train de départ.

    Cette fonction génère un dictionnaire où chaque clé est un identifiant unique
    de train (composé du numéro du train et de la date de départ), et la valeur
    correspond aux minutes écoulées depuis la date de référence pour chaque train.

    Args:
        df_sillons_dep (pd.DataFrame): DataFrame contenant les données des sillons
                                      de départ, incluant les informations sur les
                                      numéros de train, les dates et heures de départ.

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
            days_since_ref = (date_dep - Constantes.BASE_TIME).days
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
    df_sillon_dep: pd.DataFrame,
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
        df_sillon_dep (pd.DataFrame): DataFrame contenant les sillons de départ pour
                                      le traitement des données.
        dernier_depart (float): Heure du dernier départ en minutes depuis la référence.

    Returns:
        dict: Dictionnaire des limites de disponibilité des chantiers, avec des clés
              correspondant aux types de chantiers (REC, FOR, DEP) et des valeurs
              représentant les listes de limites de disponibilité.
    """
    indisponibilites_chantiers = df_chantiers[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_chantiers[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, df_sillon_dep, dernier_depart))
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
    df_sillon_dep: pd.DataFrame,
    dernier_depart: float,
) -> dict:
    indisponibilites_machines = df_machines[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_machines[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, df_sillon_dep, dernier_depart))
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
    # df_chantiers = pd.read_excel(file, sheet_name=Feuilles.CHANTIERS)

    limites_chantiers_voies = {
        Chantiers.REC: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[0]),
        Chantiers.FOR: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[1]),
        Chantiers.DEP: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[2]),
    }
    return limites_chantiers_voies


def init_dict_nombre_max_agents_sur_roulement(df_roulement_agent: pd.DataFrame) -> dict:
    n_agent = {
        r + 1: df_roulement_agent.at[r, Colonnes.NOMBRE_AGENTS]
        for r in df_roulement_agent.index
    }

    return n_agent


def init_dict_roulements_operants_sur_tache(df_roulement_agent: pd.DataFrame) -> dict:
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
    df_roulement_agent: pd.DataFrame,
    first_arr: int,
    last_dep: int,
) -> tuple[
    dict,
    dict,
    dict,
]:
    nb_roulements = df_roulement_agent.shape[0]

    delta = last_dep - first_arr
    delta_jours = ceil(delta / (4 * 24))

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

    jour_de_la_semaine = Constantes.BASE_TIME
    dernier_jour_de_la_semaine = jour_de_la_semaine + timedelta(days=delta_jours)

    h_deb0 = {i + 1: [] for i in range(nb_roulements)}

    while jour_de_la_semaine <= dernier_jour_de_la_semaine:
        for r in range(1, nb_roulements + 1):
            if (jour_de_la_semaine.weekday()) % 7 + 1 in jour_semaine_disponibilite[r]:
                h_deb0[r] += [jour_de_la_semaine + t for t in h_deb_jour[r]]
        jour_de_la_semaine += timedelta(days=1)

    nb_cycles_agents = {r: len(h_deb0[r]) for r in h_deb0}

    h_deb = {
        (r, k + 1): int((h_deb0[r][k] - Constantes.BASE_TIME).total_seconds() / 60)
        for r in range(1, nb_roulements + 1)
        for k in range(nb_cycles_agents[r])
    }

    return h_deb, nb_cycles_agents, nb_cycle_jour


def init_dicts_comp(df_roulement_agent: pd.DataFrame) -> tuple[dict, dict]:
    def extract_category(value):
        categories = []
        if "WPY_REC" in value:
            categories.append("REC")
        if "WPY_FOR" in value:
            categories.append("FOR")
        if "WPY_DEP" in value:
            categories.append("DEP")
        return categories

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
    h_deb, nb_cycles_agents, nb_cycle_jour = init_dicts_heure_debut_roulement(
        df_roulement_agent,
        first_arr,
        dernier_depart,
    )
    comp_arr, comp_dep = init_dicts_comp(df_roulement_agent)
    return (
        init_dict_t_a(df_sillons_arr),
        init_dict_t_d(df_sillons_dep),
        init_dict_correspondances(df_correspondance),
        init_dict_limites_chantiers(
            df_chantiers,
            df_sillons_dep,
            dernier_depart,
        ),
        init_dict_limites_machines(
            df_machines,
            df_sillons_dep,
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
    (
        _,
        df_sillons_arr,
        df_sillons_dep,
        df_correspondance,
        df_chantiers,
        df_machines,
        df_roulement_agent,
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
    t_arr, t_dep, occupation_REC, occupation_FOR, occupation_DEP, x_date
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
                + (Constantes.BASE_TIME + timedelta(minutes=var_arr.X)).strftime(
                    "%d/%m/%Y"
                )
                + "#A",
                "Type de tâche": "DEB",
                "Jour": (Constantes.BASE_TIME + timedelta(minutes=var_arr.X)).strftime(
                    "%d/%m/%Y"
                ),
                "Heure de début": (
                    Constantes.BASE_TIME + timedelta(minutes=var_arr.X)
                ).strftime("%H:%M"),
                "Durée": 15,
                "Sillon": n_arr
                + "#"
                + (Constantes.BASE_TIME + timedelta(minutes=var_arr.X)).strftime(
                    "%d/%m/%Y"
                )
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
                + (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                )
                + "#D",
                "Type de tâche": "FOR",
                "Jour": (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                ),
                "Heure de début": (
                    Constantes.BASE_TIME + timedelta(minutes=var_dep.X)
                ).strftime("%H:%M"),
                "Durée": 15,
                "Sillon": n_dep
                + "#"
                + (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                )
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
                + (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                )
                + "#D",
                "Type de tâche": "DEG",
                "Jour": (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                ),
                "Heure de début": (
                    Constantes.BASE_TIME + timedelta(minutes=var_dep.X)
                ).strftime("%H:%M"),
                "Durée": 20,
                "Sillon": n_dep
                + "#"
                + (Constantes.BASE_TIME + timedelta(minutes=var_dep.X)).strftime(
                    "%d/%m/%Y"
                )
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

    # Versement des trames vers la feuilles de calcul
    with pd.ExcelWriter("sortie_jalon2.xlsx", engine="openpyxl") as writer:
        df_xl.to_excel(writer, sheet_name="Taches machine", index=False)
        df_xl2.to_excel(writer, sheet_name="Occupation voie chantier", index=False)
    return True


#
