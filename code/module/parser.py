"""to parse mf excels"""

import pandas as pd
from datetime import datetime, timedelta
from constants import (
    Constantes,
    Machines,
    Chantiers,
    Feuilles,
    Colonnes,
)
from tools import convert_hour_to_minutes

# ----- dataframes ----- #


def init_df(file_path: str):
    df = pd.read_excel(file_path, sheet_name=None)

    df_sil_arr = init_sillon_arr(df)
    df_sil_dep = init_sillon_dep(df)

    df_cor = init_correspondances(df)

    return df, df_sil_arr, df_sil_dep, df_cor


def init_sillon_arr(df: pd.DataFrame) -> pd.DataFrame:
    df_sil_arr = df[Feuilles.SILLONS_ARRIVEE]
    df_sil_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sil_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_arr


def init_sillon_dep(df: pd.DataFrame) -> pd.DataFrame:
    df_sil_dep = df[Feuilles.SILLONS_DEPART]
    df_sil_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sil_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )
    return df_sil_dep


def init_correspondances(df: pd.DataFrame) -> pd.DataFrame:
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
) -> tuple[datetime, datetime, datetime]:
    first_arr = init_first_arr(df_sillons_arr)
    last_dep = init_last_dep(df_sillons_dep)

    monday = skibidi_mondays(first_arr)

    first_arr -= monday
    last_dep -= monday

    return first_arr.total_seconds() / 60, last_dep.total_seconds() / 60, monday


# ----- dicts ----- #


def init_t_a(df_sillons_arr: pd.DataFrame) -> dict:
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
        # Pour résoudre manuellement le problème sur le fichier excel de la mini_instance
    return t_a


def init_t_d(): ...


def init_dict_correspondances(): ...


def init_limites_chantiers(): ...


def init_limites_machines(): ...


def init_limites_voies(): ...


# mes enormes couillles velues balancee de facon menacante sur la table
