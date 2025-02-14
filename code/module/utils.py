"""
module description
"""

import pandas as pd


def data_open(path):
    """
    Reads an Excel file from the specified path and 
    returns sheet names and their corresponding DataFrames.

    Args:
        path (str): Path to the Excel file.

    Returns:
        tuple: A tuple containing two lists:
            - List of sheet names.
            - List of DataFrames corresponding to each sheet.
    """
    all_sheets = pd.read_excel(path, sheet_name=None)
    results = ([],[])
    for sheet_name, df in all_sheets.items():
        results[0].append(sheet_name)
        results[1].append(df)

    return results
