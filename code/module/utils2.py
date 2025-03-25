"""
Module utilitaire pour la gestion des opérations sur les trains.

Ce module fournit des classes et fonctions pour lire et traiter les données
des sillons, machines et chantiers, ainsi que pour gérer les constantes
temporelles et les feuilles de calcul. Il inclut des outils pour convertir
les heures en minutes, calculer les temps écoulés, et gérer les
indisponibilités des ressources.

Classes :
---------
Constantes : Constantes temporelles et autres valeurs fixes.
Machines : Identifiants des machines utilisées dans les opérations.
Chantiers : Identifiants des chantiers dans les opérations.
Feuilles : Noms des feuilles de calcul Excel.
Colonnes : Noms des colonnes dans les tables de données.
Taches : Constantes et attributs des tâches à effectuer sur les trains.

Fonctions :
-----------
read_sillon : Lit les feuilles 'Sillons arrivée' et 'Sillons départ'.
convert_hour_to_minutes : Convertit une heure en minutes depuis minuit.
init_t_a : Crée un dictionnaire des temps d'arrivée en minutes.
init_t_d : Crée un dictionnaire des temps de départ en minutes.
init_dict_correspondance : Crée un dictionnaire des correspondances.
dernier_depart : Calcule le temps écoulé depuis une date de référence jusqu'au dernier départ.
premiere_arrivee : Calcule le temps écoulé depuis une date de référence jusqu'à la première arrivée.
convertir_en_minutes : Convertit les plages d'indisponibilité en minutes.
traitement_doublons : Supprime les doublons consécutifs dans une liste.
creation_limites_machines : Gère les plages d'indisponibilité des machines.
creation_limites_chantiers : Gère les plages d'indisponibilité des chantiers.
base_time : Définit l'origine des temps pour les calculs.
"""

import datetime
import re
from itertools import chain
from math import *

import pandas as pd


class Constantes:
    """


    #-------- ne devrait bientot plus être utilisé --------#


    Constantes utilisées dans le module.

    Attributs :
    -----------
    BASE_TIME : pd.Timestamp
        Date de référence pour les calculs temporels.
    """

    BASE_TIME = pd.Timestamp("2022-08-08 00:00")


class Machines:
    """
    Identifiants des machines utilisées dans les opérations.

    Attributs :
    -----------
    DEB : str
        Identifiant pour les machines de début.
    FOR : str
        Identifiant pour les machines de formation.
    DEG : str
        Identifiant pour les machines de dégagement.
    """

    DEB = "DEB"
    FOR = "FOR"
    DEG = "DEG"


class Chantiers:
    """
    Identifiants des chantiers dans les opérations.

    Attributs :
    -----------
    REC : str
        Identifiant pour les chantiers de réception.
    FOR : str
        Identifiant pour les chantiers de formation.
    DEP : str
        Identifiant pour les chantiers de départ.
    """

    REC = "REC"
    FOR = "FOR"
    DEP = "DEP"


class Feuilles:
    """
    Noms des feuilles de calcul Excel utilisées.

    Attributs :
    -----------
    SILLONS_ARRIVEE : str
        Nom de la feuille des sillons d'arrivée.
    SILLONS_DEPART : str
        Nom de la feuille des sillons de départ.
    MACHINES : str
        Nom de la feuille des machines.
    CHANTIERS : str
        Nom de la feuille des chantiers.
    """

    SILLONS_ARRIVEE = "Sillons arrivee"
    SILLONS_DEPART = "Sillons depart"
    MACHINES = "Machines"
    CHANTIERS = "Chantiers"


class Colonnes:
    """
    Noms des colonnes dans les tables de données.

    Attributs :
    -----------
    SILLON_JARR : str
        Colonne du jour d'arrivée.
    SILLON_HARR : str
        Colonne de l'heure d'arrivée.
    SILLON_JDEP : str
        Colonne du jour de départ.
    SILLON_HDEP : str
        Colonne de l'heure de départ.
    SILLON_NUM_TRAIN : str
        Colonne du numéro de train.
    N_TRAIN_ARRIVEE : str
        Colonne du numéro de train d'arrivée.
    N_TRAIN_DEPART : str
        Colonne du numéro de train de départ.
    ID_TRAIN_DEPART : str
        Colonne de l'ID du train de départ.
    ID_TRAIN_ARRIVEE : str
        Colonne de l'ID du train d'arrivée.
    DATE_ARRIVEE : str
        Colonne de la date d'arrivée.
    DATE_DEPART : str
        Colonne de la date de départ.
    ID_WAGON : str
        Colonne de l'ID du wagon.
    INDISPONIBILITE : str
        Colonne des indisponibilités.
    INDISPONIBILITE_MINUTES : str
        Colonne des indisponibilités en minutes.
    """

    SILLON_JARR = "JARR"
    SILLON_HARR = "HARR"
    SILLON_JDEP = "JDEP"
    SILLON_HDEP = "HDEP"
    SILLON_NUM_TRAIN = "n°TRAIN"

    N_TRAIN_ARRIVEE = "n°Train arrivee"
    N_TRAIN_DEPART = "n°Train depart"
    ID_TRAIN_DEPART = "ID Train départ"
    ID_TRAIN_ARRIVEE = "ID Train arrivée"
    DATE_ARRIVEE = "Jour arrivee"
    DATE_DEPART = "Jour depart"
    ID_WAGON = "Id wagon"
    NOMBRE_VOIES = "Nombre de voies"

    INDISPONIBILITE = "Indisponibilites"
    INDISPONIBILITE_MINUTES = "Indisponibilites etendues en minutes"


class Taches:
    """
    Constantes des tâches à effectuer sur les trains et leur temporalité.

    Attributs :
    ----------
    TACHES_ARRIVEE : list[int]
        Tâches à effectuer à l'arrivée d'un train.
    TACHES_DEPART : list[int]
        Tâches à effectuer au départ d'un train.
    TACHES_ARR_MACHINE : list[int]
        Tâches d'arrivée nécessitant une machine.
    TACHES_DEP_MACHINE : list[int]
        Tâches de départ nécessitant une machine.
    T_ARR : dict[int, int]
        Durée des tâches d'arrivée (en minutes).
    T_DEP : dict[int, int]
        Durée des tâches de départ (en minutes).
    LIMITES : np.ndarray
        Horaires limites du chantier et des machines (en minutes).
    """

    # définition des taches
    TACHES_ARRIVEE = [1, 2, 3]
    TACHES_DEPART = [1, 2, 3, 4]

    # Définition des numéros des tâches machines
    TACHES_ARR_MACHINE = [3]
    TACHES_DEP_MACHINE = [1, 3]

    # Durée des tâches sur les trains d'arrivée
    T_ARR = {1: 15, 2: 45, 3: 15}

    # Durée des tâches sur les trains de départ
    T_DEP = {1: 15, 2: 150, 3: 15, 4: 20}


def read_sillon(file: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lit les feuilles 'Sillons arrivée' et 'Sillons départ' d'un fichier Excel.

    Convertit les dates des colonnes 'JARR' et 'JDEP' en datetime64.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des sillons.

    Retourne :
    ----------
    tuple[pd.DataFrame, pd.DataFrame]
        DataFrames des sillons d'arrivée et de départ.
    """
    df_sillons_arr = pd.read_excel(
        file, sheet_name=Feuilles.SILLONS_ARRIVEE
    )  # Arrivées
    df_sillons_dep = pd.read_excel(file, sheet_name=Feuilles.SILLONS_DEPART)  # Départs

    # Conversion des dates en datetime64
    df_sillons_arr[Colonnes.SILLON_JARR] = pd.to_datetime(
        df_sillons_arr[Colonnes.SILLON_JARR], format="%d/%m/%Y", errors="coerce"
    )
    df_sillons_dep[Colonnes.SILLON_JDEP] = pd.to_datetime(
        df_sillons_dep[Colonnes.SILLON_JDEP], format="%d/%m/%Y", errors="coerce"
    )

    return df_sillons_arr, df_sillons_dep


def convert_hour_to_minutes(hour_str: str) -> int | None:
    """
    Convertit une heure au format HH:MM en minutes depuis minuit.

    Paramètres :
    -----------
    hour_str : str
        Chaîne représentant l'heure au format HH:MM.

    Retourne :
    ----------
    int | None
        Nombre de minutes depuis minuit, ou None si la conversion échoue.
    """
    if pd.isna(hour_str) or not isinstance(hour_str, str):
        return None  # Valeur invalide
    try:
        h, m = map(int, hour_str.split(":"))
        return (h * 60) + m  # Convertir en minutes
    except ValueError:
        return None  # Si le format est incorrect


def init_t_a(df_sillons_arr: pd.DataFrame, id_file: int) -> dict:
    """
    Crée un dictionnaire t_a contenant les minutes écoulées depuis une date de
    référence pour chaque train d'arrivée.

    Paramètres :
    -----------
    df_sillons_arr : pd.DataFrame
        DataFrame contenant les données des sillons d'arrivée.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    dict
        Dictionnaire avec des identifiants uniques de trains comme clés et
        les minutes écoulées depuis la date de référence comme valeurs.
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
        # Pour résoudre manuellement le problème sur le fichier excel de la mini_instance
        if id_file == 0:
            t_a = {"1": (24 + 9) * 60, "2": (24 + 13) * 60, "3": (24 + 16) * 60}
    return t_a


def init_t_d(df_sillons_dep: pd.DataFrame, id_file: int) -> dict:
    """
    Crée un dictionnaire t_d contenant les minutes écoulées depuis une date de
    référence pour chaque train de départ.

    Paramètres :
    -----------
    df_sillons_dep : pd.DataFrame
        DataFrame contenant les données des sillons de départ.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    dict
        Dictionnaire avec des identifiants uniques de trains comme clés et
        les minutes écoulées depuis la date de référence comme valeurs.
    """
    t_d = {}
    # Traitement des départs
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
        # Pour résoudre manuellement le problème sur le fichier excel de la mini_instance
        if id_file == 0:
            t_d = {"4": (24 + 21) * 60, "5": (24 + 21) * 60, "6": (24 + 21) * 60 + 30}
    return t_d


def init_dict_correspondance(df_correspondance: pd.DataFrame, id_file: int) -> dict:
    """
    Crée un dictionnaire des correspondances entre les trains d'arrivée et de
    départ.

    Paramètres :
    -----------
    df_correspondance : pd.DataFrame
        DataFrame contenant les informations de correspondance entre les trains.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    dict
        Dictionnaire où les clés sont les identifiants des trains de départ et
        les valeurs sont des listes d'identifiants des trains d'arrivée
        correspondants.
    """
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

    if id_file == 0:
        d = {"4": ["2", "3"], "5": ["1", "2"], "6": ["1", "2", "3"]}
    return d


def dernier_depart(df_sillons_dep, base_time_value):
    """
    Calcule le temps en minutes écoulé depuis une date de référence jusqu'au
    dernier départ dans le DataFrame.

    Paramètres :
    -----------
    df_sillons_dep : pd.DataFrame
        DataFrame contenant les données des sillons de départ.
    base_time_value : pd.Timestamp
        Date de référence pour le calcul des minutes écoulées.

    Retourne :
    ----------
    float
        Temps en minutes écoulé depuis la date de référence jusqu'au dernier
        départ.
    """
    # Convertir les dates et heures en datetime
    df_sillons_dep["Datetime"] = pd.to_datetime(
        df_sillons_dep["JDEP"].astype(str) + " " + df_sillons_dep["HDEP"].astype(str)
    )

    # Trouver l'heure de départ la plus tardive
    dernier_depart_value = df_sillons_dep["Datetime"].max()

    # Calculer l'heure en minutes depuis le jour 1 à 00:00
    dernier_depart_minutes = (
        dernier_depart_value - base_time_value
    ).total_seconds() / 60

    return dernier_depart_minutes


def premiere_arrivee(df_sillons_arr, base_time_value):
    """
    Calcule le temps en minutes écoulé depuis une date de
    référence jusqu'à la première arrivée dans le DataFrame.

    Paramètres :
    -----------
    df_sillons_arr : pd.DataFrame
        DataFrame contenant les données des sillons d'arrivée.
    base_time_value : pd.Timestamp
        Date de référence pour le calcul des minutes écoulées.

    Retourne :
    ----------
    float
        Temps en minutes écoulé depuis la date de référence jusqu'au dernier
        départ.
    """
    # Convertir les dates et heures en datetime
    df_sillons_arr["Datetime"] = pd.to_datetime(
        df_sillons_arr["JDEP"].astype(str) + " " + df_sillons_arr["HDEP"].astype(str)
    )

    # Trouver l'heure de départ la plus tardive
    premiere_arrivee_value = df_sillons_arr["Datetime"].min()

    # Calculer l'heure en minutes depuis le jour 1 à 00:00
    premiere_arrivee_minutes = (
        premiere_arrivee_value - base_time_value
    ).total_seconds() / 60

    return premiere_arrivee_minutes


def convertir_en_minutes(
    indisponibilites,
    file,
    id_file,
):
    """
    Convertit une plage d'indisponibilité en minutes depuis une date de
    référence, et étend ces plages hebdomadairement jusqu'à dépasser l'heure
    du dernier train.

    Paramètres :
    -----------
    indisponibilites : str
        Chaîne contenant les plages d'indisponibilité au format
        (jour, HH:MM-HH:MM).
    file : str
        Chemin du fichier Excel contenant les données des sillons.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    list
        Liste de tuples représentant les plages d'indisponibilité en minutes
        depuis la date de référence.
    """

    _, df_sillons_dep = read_sillon(file)
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
        nouvelles_plages = [
            (deb + semaine_offset, fin + semaine_offset)
            for deb, fin in plages_originales
        ]

        # Vérifier si on a de nouvelles plages avant d'ajouter
        if not nouvelles_plages:
            break  # Évite l'accès à une liste vide

        # Ajouter les nouvelles plages
        plages_etendues.extend(nouvelles_plages)

        # Vérifier si la dernière plage dépasse l'heure du dernier train
        if nouvelles_plages[-1][1] > dernier_depart(df_sillons_dep, base_time(id_file)):
            break

        semaine += 1  # Passer à la semaine suivante

    return plages_etendues


def traitement_doublons(liste):
    """
    Supprime les doublons consécutifs dans une liste de listes.

    Paramètres :
    -----------
    liste : list
        Liste contenant des sous-listes d'éléments à traiter.

    Retourne :
    ----------
    list
        Liste avec les doublons consécutifs retirés dans chaque sous-liste.
    """
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


def creation_limites_machines(file: str, id_file: int) -> dict:
    """
    Convertit les plages d'indisponibilité des machines en minutes et les
    organise dans un dictionnaire.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des machines.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    dict
        Dictionnaire contenant les plages d'indisponibilité en minutes pour
        chaque machine (DEB, FOR, DEG).
    """

    df_machines = pd.read_excel(file, sheet_name=Feuilles.MACHINES)

    indisponibilites_machines = df_machines[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_machines[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, file, id_file))
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


def creation_limites_chantiers(file: str, id_file: int) -> dict:
    """
    Convertit les plages d'indisponibilité des chantiers en minutes et les
    organise dans un dictionnaire.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    dict
        Dictionnaire contenant les plages d'indisponibilité en minutes pour
        chaque chantier (REC, FOR, DEP).
    """

    df_chantiers = pd.read_excel(file, sheet_name=Feuilles.CHANTIERS)

    indisponibilites_chantiers = df_chantiers[Colonnes.INDISPONIBILITE_MINUTES] = (
        df_chantiers[Colonnes.INDISPONIBILITE]
        .astype(str)
        .apply(lambda x: convertir_en_minutes(x, file, id_file))
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


def base_time(id_file: int) -> pd.Timestamp:
    """
    Définit l'origine des temps au premier lundi précédant les événements de
    l'instance, en fonction de l'identifiant du fichier.

    Paramètres :
    -----------
    id_file : int
        Identifiant du fichier pour déterminer la date de référence.

    Retourne :
    ----------
    pd.Timestamp
        Date de référence pour le calcul des minutes écoulées.
    """
    if id_file == 0:
        return pd.Timestamp("2023-05-01 00:00")
    else:
        return pd.Timestamp("2022-08-08 00:00")


def init_limites_voies(file: str):
    """
    Définit le nombre de voies utilisables au maximum sur les différents chantiers.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.

    Retourne :
    ----------
    dict
        Dictionnaire contenant le nombre maximal de voies utilisables pour
        chaque chantier (REC, FOR, DEP).
    """
    df_chantiers = pd.read_excel(file, sheet_name=Feuilles.CHANTIERS)

    limites_chantiers_voies = {
        Chantiers.REC: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[0]),
        Chantiers.FOR: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[1]),
        Chantiers.DEP: int(df_chantiers[Colonnes.NOMBRE_VOIES].astype(str)[2]),
    }
    return limites_chantiers_voies


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
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_arr.X)
                ).strftime("%d/%m/%Y")
                + "#A",
                "Type de tâche": "DEB",
                "Jour": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_arr.X)
                ).strftime("%d/%m/%Y"),
                "Heure de début": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_arr.X)
                ).strftime("%H:%M"),
                "Durée": 15,
                "Sillon": n_arr
                + "#"
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_arr.X)
                ).strftime("%d/%m/%Y")
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
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y")
                + "#D",
                "Type de tâche": "FOR",
                "Jour": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y"),
                "Heure de début": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%H:%M"),
                "Durée": 15,
                "Sillon": n_dep
                + "#"
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y")
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
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y")
                + "#D",
                "Type de tâche": "DEG",
                "Jour": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y"),
                "Heure de début": (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%H:%M"),
                "Durée": 20,
                "Sillon": n_dep
                + "#"
                + (
                    Constantes.BASE_TIME + datetime.timedelta(minutes=var_dep.X)
                ).strftime("%d/%m/%Y")
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


def nombre_roulements(file: str) -> int:
    """
    Fonction qui retourne le nombre de roulements d'agents différents.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.

    Retourne :
    ---------
    int
        Nombre de roulements d'agents différents.
    """
    df = pd.read_excel(file, sheet_name="Roulements agents")
    count = df["Roulement"].count()

    return count


def nombre_max_agents_sur_roulement(file: str) -> dict:
    """
    Fonction qui définie un dictionnaire associant à chaque type de roulement d'agents le nombre d'agents disponibles quotidiennement.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.

    Retourne :
    ---------
    dict
        Dictionnaire associant à chaque roulement d'agent le nombre d'agents disponibles quotidiennement.
    """
    df = pd.read_excel(file, sheet_name="Roulements agents")

    n_agent = {r + 1: df.at[r, "Nombre agents"] for r in df.index}

    return n_agent


def roulements_operants_sur_tache(file: str) -> dict:
    df = pd.read_excel(file, sheet_name="Roulements agents")

    roulements_operants_sur_m = {}
    for m in [1, 2, 3]:
        roulements_operants_sur_m[("arr", m)] = (
            df[df["Connaissances chantiers"].str.contains("REC", na=False)].index + 1
        ).tolist()
        roulements_operants_sur_m[("dep", m)] = (
            df[df["Connaissances chantiers"].str.contains("FOR", na=False)].index + 1
        ).tolist()
    for m in [4]:
        roulements_operants_sur_m[("dep", m)] = (
            df[df["Connaissances chantiers"].str.contains("DEP", na=False)].index + 1
        ).tolist()
    return roulements_operants_sur_m


def heure_debut_roulement(file: str, temps_min: int, temps_max: int) -> dict:
    """
    Retourne un dictionnaire contenant le nombre de cycles possibles sur toute la durée étudiée pour chaque roulement d'agents.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.
    temps_min : int
        Heure d'arrivée du premier train (permet de réduire le nombre de variables à créer).
    temps_max : int
        Heure de départ du dernier train (permet de réduire le nombre de variables à créer).

    Retourne :
    ---------
    dict
        Dictionnaire contenant le nombre de cycles possibles sur toute la durée étudiée pour chaque roulement d'agents.
    """

    df = pd.read_excel(file, sheet_name="Roulements agents")
    nb_roulements = df.shape[0]

    delta = temps_max - temps_min
    delta_jours = ceil(delta / (4 * 24))

    jour_semaine_disponibilite = {
        i + 1: [int(x) for x in str(row).split(";")]
        for i, row in enumerate(df["Jours de la semaine"].dropna())
    }

    h_deb_jour = {
        i + 1: sorted(
            [
                datetime.timedelta(hours=int(x[:2]), minutes=int(x[3:5]))
                for x in str(row).split(";")
            ]
        )
        for i, row in enumerate(df["Cycles horaires"].dropna())
    }
    
    nb_cycle_jour={r : len(h_deb_jour[r]) for r in h_deb_jour}

    jour_de_la_semaine = Constantes.BASE_TIME
    dernier_jour_de_la_semaine = jour_de_la_semaine + datetime.timedelta(
        days=delta_jours
    )

    h_deb0 = {i + 1: [] for i in range(nb_roulements)}

    while jour_de_la_semaine <= dernier_jour_de_la_semaine:
        for r in range(1, nb_roulements + 1):
            if (jour_de_la_semaine.weekday())%7+1 in jour_semaine_disponibilite[r]:
                h_deb0[r] += [jour_de_la_semaine + t for t in h_deb_jour[r]]
        jour_de_la_semaine += datetime.timedelta(days=1)
    print(h_deb0)

    nb_cycles_agents = {r: len(h_deb0[r]) for r in h_deb0}

    h_deb = {
        (r, k + 1): int((h_deb0[r][k] - Constantes.BASE_TIME).total_seconds() / 60)
        for r in range(1, nb_roulements + 1)
        for k in range(nb_cycles_agents[r])
    }

    return h_deb, nb_cycles_agents, nb_cycle_jour

    # def heure_debut_roulement(file: str, nb_cycles: dict, nb_roulements: int) -> dict:
    """
    Retourne un dictionnaire associant à un roulement r et un cycle k l'heure de début de celui-ci, comptée à partir de la base temporelle.

    Paramètres :
    -----------
    file : str
        Chemin du fichier Excel contenant les données des chantiers.
    nombre_cycles : dict
        Dictionnaire contenant le nombre de cycles possibles sur toute la durée étudiée pour chaque roulement d'agents.
    nombre_roulements : int
        Nombre de roulements d'agents différents.

    Retourne :
    ---------
    dict
        Dictionnaire associant à un roulement r et un cycle k l'heure de début de celui-ci.
    """


#    df = pd.read_excel(file, sheet_name="Roulements agents")

#    h_deb = {}
#    for r in range(1, nb_roulements + 1):
#        for k in range(1, nb_cycles[r] + 1):
#            mod = len(str(df.at[r - 1, "Cycles horaires"]).split(";"))
#            h_deb[(r, k)] = (
#                int(
#                    str(df.at[r - 1, "Cycles horaires"])
#                    .split(";")[k % mod - 1]
#                    .split("-")[0]
#                    .split(":")[0]
#                )
#                + (k - 1) // mod * 24
#            )

#    return h_deb


def comp(file):
    df = pd.read_excel(file, sheet_name="Roulements agents")

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

    for r in range(1, len(df) + 1):
        comp_arr[r] = []
        comp_dep[r] = []
        value = str(df.loc[r - 1, "Connaissances chantiers"])
        if "WPY_REC" in value:
            comp_arr[r] += [1, 2, 3]
        if "WPY_FOR" in value:
            comp_dep[r] += [1, 2, 3]
        if "WPY_DEP" in value:
            comp_dep[r] += [4]

    return comp_arr, comp_dep
