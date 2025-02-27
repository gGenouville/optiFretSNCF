"""
module docstring
"""

import pandas as pd

class Feuille:
    """
    Class to store the names of the shits.
    """
    CHANTIER = 'Chantiers'
    MACHINES = 'Machines'
    CORRESPONDANCES = 'Correspondances'
    TACHES_HUMAINES = 'Taches humaines'
    SILLON_ARRIVEE = 'Sillons arrivee'
    SILLON_DEPART = 'Sillons depart'
    ROULEMENTS = 'Roulements agents'

class Colonne :
    """
    Class to store the names of the columns in a df
    """
    N_TRAIN_ARRIVEE = 'n°Train arrivee'
    N_TRAIN_DEPART = 'n°Train depart'

def data_open(path:str)->dict[str,pd.DataFrame]:
    """
    Reads an Excel file from the specified path and 
    returns a dictionary of sheet names and their 
    corresponding DataFrames.

    Args:
        path (str): Path to the Excel file.

    Returns:
        dict: A dictionary where keys are sheet names and 
            values are DataFrames corresponding to each sheet.
    """
    all_sheets = pd.read_excel(path, sheet_name=None)
    results = {}
    for sheet_name, df in all_sheets.items():
        results[sheet_name] = df
    return results

def get_link_id(arrival_train_id, departure_train_id):
    """
    creates an id for a link
    """
    return f"{arrival_train_id} {departure_train_id}"

def init_dict_correspondance(df_correspondance : pd.dataFrame)-> dict:
    # completer

    


def init_model():
    ...

def init_contr():
    ...

