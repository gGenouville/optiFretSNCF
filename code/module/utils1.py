""" """

import pandas as pd
import re
from itertools import chain


class Constantes:
    """constantes"""
    # Définition de la base temporelle (08/08/2022 à minuit)
    BASE_TIME = pd.Timestamp("2022-08-08 00:00")


class Feuilles:
    """ feuilles des tables"""
    SILLONS_ARRIVEE = "Sillons arrivee"
    SILLONS_DEPART = "Sillons depart"


class Colonnes:
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


def read_sillon(file: str) -> (pd.DataFrame, pd.DataFrame):
    """Lire les feuilles 'Sillons arrivée' et 'Sillons départ'"""
    df_sillons_arr = pd.read_excel(
        file, sheet_name=Feuilles.SILLONS_ARRIVEE)  # Arrivées
    df_sillons_dep = pd.read_excel(
        file, sheet_name=Feuilles.SILLONS_DEPART)  # Départs

    # Conversion des dates en datetime64
    df_sillons_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sillons_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    df_sillons_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sillons_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )

    return df_sillons_arr, df_sillons_dep


# Fonction pour convertir une heure en minutes
def convert_hour_to_minutes(hour_str: str) -> int | None:
    """Convertit une heure HH:MM en minutes depuis minuit."""
    if pd.isna(hour_str) or not isinstance(hour_str, str):
        return None  # Valeur invalide
    try:
        h, m = map(int, hour_str.split(":"))
        return (h * 60) + m  # Convertir en minutes
    except ValueError:
        return None  # Si le format est incorrect


# Traitement des arrivées
def init_t_a(df_sillons_arr: pd.DataFrame, print_bool: bool = True) -> dict:
    """creer t_a"""
    t_a = {}
    for _, row in df_sillons_arr.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_arr = row[Colonnes.SILLON_JARR]
        heure_arr = convert_hour_to_minutes(
            row[Colonnes.SILLON_HARR])  # Conversion heure → minutes

        if pd.notna(date_arr) and heure_arr is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_arr - Constantes.BASE_TIME).days
            minutes_since_ref = (days_since_ref * 1440) + \
                heure_arr  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date, car certains trains portant le même ID passent sur des jours différents
            train_id_unique = f"{train_id}_{date_arr.strftime('%d')}"

            t_a[train_id_unique] = minutes_since_ref
            if print_bool:
                print(
                    f"Train {train_id_unique} : {Colonnes.SILLON_JARR} = {date_arr.date()}, minutes écoulées = {minutes_since_ref}"
                )
    return t_a


# Traitement des départs
def init_t_d(df_sillons_dep: pd.DataFrame, print_bool: bool = True) -> dict:
    """creer t_d"""
    t_d = {}
    # Traitement des départs
    for _, row in df_sillons_dep.iterrows():
        train_id = row[Colonnes.SILLON_NUM_TRAIN]
        date_dep = row[Colonnes.SILLON_JDEP]
        heure_dep = convert_hour_to_minutes(
            row[Colonnes.SILLON_HDEP])  # Conversion heure → minutes

        if pd.notna(date_dep) and heure_dep is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_dep - Constantes.BASE_TIME).days
            minutes_since_ref = (days_since_ref * 1440) + \
                heure_dep  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date
            train_id_unique = f"{train_id}_{date_dep.strftime('%d')}"

            t_d[train_id_unique] = minutes_since_ref

            if print_bool:
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


def dernier_depart(df_sillons_dep, base_time):
    # Convertir les dates et heures en datetime
    df_sillons_dep["Datetime"] = pd.to_datetime(
        df_sillons_dep["JDEP"].astype(str) + " " + df_sillons_dep["HDEP"].astype(str))

    # Trouver l'heure de départ la plus tardive
    dernier_depart = df_sillons_dep["Datetime"].max()

    # Calculer l'heure en minutes depuis le jour 1 à 00:00
    dernier_depart_minutes = (dernier_depart - base_time).total_seconds() / 60

    return dernier_depart_minutes

# Fonction pour convertir une plage d'indisponibilité en minutes depuis J1 00:00


def convertir_en_minutes(indisponibilites, df_sillons_dep):
    pattern = r"\((\d+),\s*(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})\)"
    plages_originales = []

    for match in re.finditer(pattern, indisponibilites):
        jour = int(match.group(1))
        debut_h, debut_m = int(match.group(2)), int(match.group(3))
        fin_h, fin_m = int(match.group(4)), int(match.group(5))

        debut_minutes = (jour - 1) * 1440 + debut_h * 60 + debut_m
        fin_minutes = (jour - 1) * 1440 + fin_h * 60 + fin_m

        plages_originales.append((debut_minutes, fin_minutes))

    # Si aucune plage trouvée, retourner une liste vide
    if not plages_originales:
        return []

    # Étendre les indisponibilités chaque semaine jusqu'à dépasser l'heure du dernier train
    plages_etendues = []
    semaine = 0
    while True:
        semaine_offset = semaine * 10080  # 7 jours en minutes
        nouvelles_plages = [(deb + semaine_offset, fin + semaine_offset)
                            for deb, fin in plages_originales]

        # Vérifier si on a de nouvelles plages avant d'ajouter
        if not nouvelles_plages:
            break  # Évite l'accès à une liste vide

        # Ajouter les nouvelles plages
        plages_etendues.extend(nouvelles_plages)

        # Vérifier si la dernière plage dépasse l'heure du dernier train
        if nouvelles_plages[-1][1] > dernier_depart(df_sillons_dep, base_time):
            break

        semaine += 1  # Passer à la semaine suivante

    return plages_etendues


def traitement_doublons(liste):
    resultat = []
    for elmt in liste:
        resultat_int = []
        i = 0
        while i < len(elmt):
            if i < len(elmt) - 1 and elmt[i] == elmt[i + 1]:
                i += 2  # On saute les deux éléments consécutifs égaux
            else:
                resultat_int.append(elmt[i])
                i += 1  # On avance normalement si pas de doublon
        resultat.append(resultat_int)
    return resultat


def creation_limites_machines(df_machines: pd.DataFrame) -> dict:

    # Appliquer la conversion à la colonne "Indisponibilites"
    Indisponibilités_machines = df_machines["Indisponibilites etendues en minutes"] = df_machines["Indisponibilites"].astype(
        str).apply(convertir_en_minutes)

    listes_plates_machines = Indisponibilités_machines.apply(
        lambda x: list(chain(*x)))

    Limites_machines = []
    for i, liste in enumerate(listes_plates_machines):
        Limites_machines.append(liste)

    Limites_machines = traitement_doublons(Limites_machines)
    Limites_machines = {
        'DEB': Limites_machines[0], 'FOR': Limites_machines[1], 'DEG': Limites_machines[2]}

    return Limites_machines


def creation_limites_chantiers(df_chantiers: pd.DataFrame):
    # Appliquer la conversion à la colonne "Indisponibilites"
    Indisponibilités_chantiers = df_chantiers["Indisponibilites etendues en minutes"] = df_chantiers["Indisponibilites"].astype(
        str).apply(convertir_en_minutes)

    listes_plates_chantiers = Indisponibilités_chantiers.apply(
        lambda x: list(chain(*x)))

    Limites_chantiers = []
    for i, liste in enumerate(listes_plates_chantiers):
        Limites_chantiers.append(liste)

    Limites_chantiers = traitement_doublons(Limites_chantiers)

    Limites_chantiers = {
        'REC': Limites_chantiers[0], 'FOR': Limites_chantiers[1], 'DEP': Limites_chantiers[2]}


def base_time(id_file):
    if id_file == 0:
        return (pd.Timestamp("2023-05-01 00:00"))
    elif id_file == 1:
        return (pd.Timestamp("2022-08-08 00:00"))
