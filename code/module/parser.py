"""to parse mf excels"""

import pandas as pd
from datetime import datetime, timedelta
from itertools import chain
from constants import (
    Constantes,
    Machines,
    Chantiers,
    Feuilles,
    Colonnes,
)
from tools import (
    convert_hour_to_minutes,
    convertir_en_minutes,
    traitement_doublons,
)

# ----- dataframes ----- #


def init_dfs(file_path: str):
    df = pd.read_excel(file_path, sheet_name=None)

    df_sil_arr = init_df_sillon_arr(df)
    df_sil_dep = init_df_sillon_dep(df)

    df_cor = init_df_correspondances(df)

    df_chantiers = df[Feuilles.CHANTIERS]
    df_machines = df[Feuilles.MACHINES]

    return (
        df,
        df_sil_arr,
        df_sil_dep,
        df_cor,
        df_chantiers,
        df_machines,
    )


def init_df_sillon_arr(df: pd.DataFrame) -> pd.DataFrame:
    df_sil_arr = df[Feuilles.SILLONS_ARRIVEE]
    df_sil_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sil_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_arr


def init_df_sillon_dep(df: pd.DataFrame) -> pd.DataFrame:
    df_sil_dep = df[Feuilles.SILLONS_DEPART]
    df_sil_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sil_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_dep


def init_df_correspondances(df: pd.DataFrame) -> pd.DataFrame:
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
    d = {}
    for departure_train_id in input_df[Colonnes.ID_TRAIN_DEPART]:
        d[departure_train_id] = []
    for arrival_train_id, departure_train_id in zip(
        input_df[Colonnes.ID_TRAIN_ARRIVEE],
        input_df[Colonnes.ID_TRAIN_DEPART],
    ):
        d[departure_train_id].append(arrival_train_id)

    return d


# ----- values ----- #


def skibidi_mondays(date: datetime) -> datetime:
    jour_semaine = date.weekday()
    delta = timedelta(days=jour_semaine)
    return date - delta


def init_first_arr(df_sillons_arr: pd.Dataframe) -> datetime:
    df_sillons_arr["Datetime"] = pd.to_datetime(
        df_sillons_arr["JDEP"].astype(str) + " " + df_sillons_arr["HDEP"].astype(str)
    )
    return df_sillons_arr["Datetime"].min()


def init_last_dep(df_sillons_dep: pd.DataFrame) -> datetime:
    df_sillons_dep["Datetime"] = pd.to_datetime(
        df_sillons_dep["JDEP"].astype(str) + " " + df_sillons_dep["HDEP"].astype(str)
    )
    return df_sillons_dep["Datetime"].max()


def init_values(
    df_sillons_arr: pd.DataFrame,
    df_sillons_dep: pd.DataFrame,
) -> tuple[float, float, datetime]:
    first_arr = init_first_arr(df_sillons_arr)
    last_dep = init_last_dep(df_sillons_dep)

    monday = skibidi_mondays(first_arr)

    first_arr -= monday
    last_dep -= monday

    return first_arr.total_seconds() / 60, last_dep.total_seconds() / 60, monday


# ----- dicts ----- #


def init_dict_t_a(df_sillons_arr: pd.DataFrame) -> dict:
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
    input_df = df_correspondance.astype(str)
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
    # df_chantiers = pd.read_excel(file, sheet_name=Feuilles.CHANTIERS)

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
    # df_machines = pd.read_excel(file, sheet_name=Feuilles.MACHINES)
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


def init_dicts(
    file_path: str,
) -> tuple[
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
]:
    (
        _,
        df_sillons_arr,
        df_sillons_dep,
        df_correspondance,
        df_chantiers,
        df_machines,
    ) = init_dfs(file_path)

    first_arr, dernier_depart, monday = init_values(
        df_sillons_arr,
        df_sillons_dep,
    )
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
    )


# mes enormes couillles velues balancee de facon menacante sur la table
