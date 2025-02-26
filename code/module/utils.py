"""
module docstring
"""

import pandas as pd

class ColonnesInstance:
    """
    Class to store the names of the columns in the instance data.
    """
    CHANTIER = 'Chantiers'
    MACHINES = 'Machines'
    CORRESPONDANCES = 'Correspondances'
    TACHES_HUMAINES = 'Taches humaines'
    SILLON_ARRIVEE = 'Sillons arrivee'
    SILLON_DEPART = 'Sillons depart'
    ROULEMENTS = 'Roulements agents'


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


def init_model():
    ...

def init_contr():
    ...

