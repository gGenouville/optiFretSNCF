import numpy as np
import os
import sys
import pandas as pd


def creation_listes_temps_arrivee_depart(file):
    module_path = os.path.abspath(os.path.join('..', 'module'))
    sys.path.append(module_path)

    # Définition de la base temporelle (08/08/2022 à minuit)
    base_time = pd.Timestamp("2022-08-08 00:00")

    # Lire les feuilles "Sillons arrivée" et "Sillons départ"
    df_sillons_arr = pd.read_excel(
        file, sheet_name="Sillons arrivee")  # Arrivées
    df_sillons_dep = pd.read_excel(
        file, sheet_name="Sillons depart")  # Départs

    # Conversion des dates en datetime64
    df_sillons_arr["JARR"] = pd.to_datetime(
        df_sillons_arr["JARR"], format="%d/%m/%Y", errors="coerce")
    df_sillons_dep["JDEP"] = pd.to_datetime(
        df_sillons_dep["JDEP"], format="%d/%m/%Y", errors="coerce")

    # Fonction pour convertir une heure en minutes
    def convert_hour_to_minutes(hour_str):
        """Convertit une heure HH:MM en minutes depuis minuit."""
        if pd.isna(hour_str) or not isinstance(hour_str, str):
            return None  # Valeur invalide
        try:
            h, m = map(int, hour_str.split(":"))
            return (h * 60) + m  # Convertir en minutes
        except ValueError:
            return None  # Si le format est incorrect

    # Dictionnaires pour stocker les temps d'arrivée et de départ en minutes
    t_a = {}
    t_d = {}

    # Traitement des arrivées
    for _, row in df_sillons_arr.iterrows():
        train_id = row["n°TRAIN"]
        date_arr = row["JARR"]
        heure_arr = convert_hour_to_minutes(
            row["HARR"])  # Conversion heure → minutes

        if pd.notna(date_arr) and heure_arr is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_arr - base_time).days
            minutes_since_ref = (days_since_ref * 1440) + \
                heure_arr  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date, car certains trains portant le même ID passent sur des jours différents
            train_id_unique = f"{train_id}_{date_arr.strftime('%d')}"

            t_a[train_id_unique] = minutes_since_ref

    # Traitement des départs
    for _, row in df_sillons_dep.iterrows():
        train_id = row["n°TRAIN"]
        date_dep = row["JDEP"]
        heure_dep = convert_hour_to_minutes(
            row["HDEP"])  # Conversion heure → minutes

        if pd.notna(date_dep) and heure_dep is not None:
            # Nombre de jours depuis le 08/08
            days_since_ref = (date_dep - base_time).days
            minutes_since_ref = (days_since_ref * 1440) + \
                heure_dep  # Ajout des minutes

            # Création d'un ID unique : Train_ID_Date
            train_id_unique = f"{train_id}_{date_dep.strftime('%d')}"

            t_d[train_id_unique] = minutes_since_ref

    return (t_a, t_d)
