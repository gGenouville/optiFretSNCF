""" """

import pandas as pd


class Constantes:
    """constantes"""
    # Définition de la base temporelle (08/08/2022 à minuit)
    BASE_TIME = pd.Timestamp("2022-08-08 00:00")

class Feuilles :
    """ feuilles des tables"""
    SILLONS_ARRIVEE = "Sillons arrivee"
    SILLONS_DEPART = "Sillons depart"


class Colonnes :
    """colonnes des tables"""

    SILLON_JARR = "JARR"
    SILLON_HARR = "HARR"
    SILLON_JDEP = "JDEP"
    SILLON_HDEP = "HDEP"
    SILLON_NUM_TRAIN = "n°TRAIN"

    N_TRAIN_ARRIVEE = 'n°Train arrivee'
    N_TRAIN_DEPART = 'n°Train depart'
    ID_TRAIN_DEPART = 'ID Train départ'
    ID_TRAIN_ARRIVEE = 'ID Train arrivée'
    DATE_ARRIVEE = "Jour arrivee"
    DATE_DEPART = "Jour depart"
    ID_WAGON = "Id wagon"

def read_sillon(file:str)->(pd.DataFrame,pd.DataFrame):
    """Lire les feuilles 'Sillons arrivée' et 'Sillons départ'"""
    df_sillons_arr = pd.read_excel(file, sheet_name=Feuilles.SILLONS_ARRIVEE)  # Arrivées
    df_sillons_dep = pd.read_excel(file, sheet_name=Feuilles.SILLONS_DEPART)  # Départs

    # Conversion des dates en datetime64
    df_sillons_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sillons_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    df_sillons_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sillons_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )

    return df_sillons_arr, df_sillons_dep


# Fonction pour convertir une heure en minutes
def convert_hour_to_minutes(hour_str:str)->int|None:
    """Convertit une heure HH:MM en minutes depuis minuit."""
    if pd.isna(hour_str) or not isinstance(hour_str, str):
        return None  # Valeur invalide
    try:
        h, m = map(int, hour_str.split(":"))
        return (h * 60) + m  # Convertir en minutes
    except ValueError:
        return None  # Si le format est incorrect


# Traitement des arrivées
def init_t_a(df_sillons_arr:pd.DataFrame, print_bool:bool=True)->dict:
    """creer t_a"""
    t_a = {}
    for _, row in df_sillons_arr.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_arr = row[Colonnes.SILLON_JARR]
        heure_arr = convert_hour_to_minutes(row[Colonnes.SILLON_HARR])  # Conversion heure → minutes

        if pd.notna(date_arr) and heure_arr is not None:
            days_since_ref = (date_arr - Constantes.BASE_TIME).days  # Nombre de jours depuis le 08/08
            minutes_since_ref = (days_since_ref * 1440) + heure_arr  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date, car certains trains portant le même ID passent sur des jours différents
            train_id_unique = f"{train_id}_{date_arr.strftime('%d')}"

            t_a[train_id_unique] = minutes_since_ref
            if print_bool:
                print(
                    f"Train {train_id_unique} : {Colonnes.SILLON_JARR} = {date_arr.date()}, minutes écoulées = {minutes_since_ref}"
                )
    return t_a


# Traitement des départs
def init_t_d(df_sillons_dep:pd.DataFrame, print_bool:bool=True)->dict:
    """creer t_d"""
    t_d = {}
    # Traitement des départs
    for _, row in df_sillons_dep.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_dep = row[Colonnes.SILLON_JDEP]
        heure_dep = convert_hour_to_minutes(row[Colonnes.SILLON_HDEP])  # Conversion heure → minutes

        if pd.notna(date_dep) and heure_dep is not None:
            days_since_ref = (date_dep - Constantes.BASE_TIME).days  # Nombre de jours depuis le 08/08
            minutes_since_ref = (days_since_ref * 1440) + heure_dep  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date
            train_id_unique = f"{train_id}_{date_dep.strftime('%d')}"

            t_d[train_id_unique] = minutes_since_ref

            if print_bool :
                print(
                    f"Train {train_id_unique} : {Colonnes.SILLON_JDEP} = {date_dep.date()}, minutes écoulées = {minutes_since_ref}"
                )
    return t_d


def init_dict_correspondance(df_correspondance: pd.DataFrame) -> dict:
    """Dictionnaires des correspondances"""
    input_df = df_correspondance.astype(str)

    input_df[Colonnes.ID_TRAIN_ARRIVEE] = (
        input_df[Colonnes.N_TRAIN_ARRIVEE]
        + "_"
        + pd.to_datetime(input_df[Colonnes.DATE_ARRIVEE],
                         format="%d/%m/%Y", errors="coerce").dt.strftime('%d')
    )

    input_df[Colonnes.ID_TRAIN_DEPART] = (
        input_df[Colonnes.N_TRAIN_DEPART]
        + "_"
        + pd.to_datetime(input_df[Colonnes.DATE_DEPART],
                         format="%d/%m/%Y", errors="coerce").dt.strftime('%d')
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