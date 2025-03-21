"""rplaces utils module to concentrate on the quick tools (no data )"""

import pandas as pd


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
