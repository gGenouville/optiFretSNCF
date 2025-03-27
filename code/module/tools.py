"""
Sous-module utilitaire.

Ce module fournit des fonctions pour convertir des plages d'indisponibilités
en minutes, supprimer les doublons dans des sous-listes, et convertir des
heures au format "hh:mm" en minutes.

Fonctions :
- convertir_en_minutes(indisponibilites: str, df_sillon_dep: pd.DataFrame,
                       dernier_depart: float) -> list:
    Convertit les plages d'indisponibilités en minutes et les étend chaque
    semaine jusqu'à dépasser l'heure du dernier train.

- traitement_doublons(liste: list) -> list:
    Supprime les éléments consécutifs identiques dans chaque sous-liste
    d'une liste donnée.

- convert_hour_to_minutes(hour_str: str) -> int | None:
    Convertit une chaîne représentant une heure au format "hh:mm" en
    minutes.
"""

import re
import pandas as pd


def convert_hour_to_minutes(hour_str: str) -> int | None:
    """
    Convertit une chaîne représentant une heure au format "hh:mm" en
    minutes.

    Args:
        hour_str (str): Chaîne représentant une heure au format "hh:mm".

    Returns:
        int | None: Nombre total de minutes ou None si la chaîne est
            invalide ou mal formatée.
    """
    if pd.isna(hour_str) or not isinstance(hour_str, str):
        return None  # Valeur invalide
    try:
        h, m = map(int, hour_str.split(":"))
        return (h * 60) + m  # Convertir en minutes
    except ValueError:
        return None  # Si le format est incorrect


def convertir_en_minutes(
    indisponibilites: str,
    dernier_depart: float,
) -> list:
    """
    Convertit les plages d'indisponibilités en minutes et les étend
    chaque semaine jusqu'à dépasser l'heure du dernier train.

    Args:
        indisponibilites (str): Chaîne contenant les plages
            d'indisponibilités au format "(jour, hh:mm-hh:mm)".
        df_sillon_dep (pd.DataFrame): DataFrame contenant les
            informations de départ. Non utilisé dans cette fonction.
        dernier_depart (float): Heure du dernier départ en minutes.

    Returns:
        list: Liste de tuples représentant les plages
            d'indisponibilités en minutes, étendues chaque semaine.
    """
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
        if nouvelles_plages[-1][1] > dernier_depart:
            break

        semaine += 1  # Passer à la semaine suivante

    return plages_etendues


def traitement_doublons(liste: list) -> list:
    """
    Supprime les éléments consécutifs identiques dans chaque sous-liste
    d'une liste donnée.

    Args:
        liste (list): Liste contenant des sous-listes d'éléments.

    Returns:
        list: Nouvelle liste avec les éléments consécutifs identiques
            supprimés dans chaque sous-liste.
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


#
