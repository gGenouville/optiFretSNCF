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
    ID_TRAIN_DEPART = 'ID Train départ'
    ID_TRAIN_ARRIVEE = 'ID Train arrivée'
    DATE_ARRIVEE = "Jour arrivee"
    DATE_DEPART = "Jour depart"
    ID_WAGON = "Id wagon"

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

def init_dict_correspondance(df_correspondance : pd.DataFrame)-> dict:
    input_df=df_correspondance.astype(str)

    input_df[Colonne.ID_TRAIN_ARRIVEE] = (
        input_df[Colonne.N_TRAIN_ARRIVEE]
        + "_"
        + pd.to_datetime(input_df[Colonne.DATE_ARRIVEE], format="%d/%m/%Y", errors="coerce").dt.strftime('%d')
    )

    input_df[Colonne.ID_TRAIN_DEPART] = (
            input_df[Colonne.N_TRAIN_DEPART]
            + "_"
            + pd.to_datetime(input_df[Colonne.DATE_DEPART], format="%d/%m/%Y", errors="coerce").dt.strftime('%d')
    )
    d={}
    for departure_train_id in input_df[Colonne.ID_TRAIN_DEPART]:
        d[departure_train_id]=[]
    for arrival_train_id, departure_train_id in zip(
        input_df[Colonne.ID_TRAIN_ARRIVEE],
        input_df[Colonne.ID_TRAIN_DEPART],
    ):
        d[departure_train_id].append(arrival_train_id)
    return d

    


    def init_model():
        ...

    def init_contr():
        ...

