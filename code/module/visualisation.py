"""
Module de visualisation de solutions d'attribution des créneaux des tâches.

Fonctions :
-----------
visualisation_gantt : Prépare la visualisation du diagramme de Gantt des tâches.
visualisation_occupation : Prépare la visualisation de l'occupation des voies de chantier.
"""

import itertools
from datetime import timedelta, datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from module.constants import Taches


def visualisation_gantt(t_arr: dict, t_dep: dict, monday: datetime) -> Figure:
    """
    Prépare la visualisation du diagramme de Gantt des tâches.

    Paramètres :
    -----------
    t_arr : dict
        Variables de début des tâches d'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.

    Retourne :
    ---------
    fig
        Trace le diagramme de Gantt.
    """
    # Liste ordonnée des machines
    ordered_machines = ["arr_1", "arr_2", "arr_3", "dep_1", "dep_2", "dep_3", "dep_4"]

    # Données fournies sous forme de liste de dictionnaires
    tasks = [
        {
            "Train": n_arr,
            "Start": monday + timedelta(minutes=15 * var_arr.X),
            "Finish": monday
            + timedelta(minutes=15 * var_arr.X + Taches.T_ARR[m_arr]),
            "Machine": f"arr_{m_arr}",
            "Tâches": f"arr_{m_arr}",
        }
        for (m_arr, n_arr), var_arr in t_arr.items()
    ] + [
        {
            "Train": n_dep,
            "Start": monday + timedelta(minutes=15 * var_dep.X),
            "Finish": monday
            + timedelta(minutes=15 * var_dep.X + Taches.T_DEP[m_dep]),
            "Machine": f"dep_{m_dep}",
            "Tâches": f"dep_{m_dep}",
        }
        for (m_dep, n_dep), var_dep in t_dep.items()
    ]

    # Construction du DataFrame pour la visualisation
    gantt_df = pd.DataFrame(tasks)

    # Regroupement des ressources par machine
    resource_per_machine = {}
    for task in tasks:
        resource_per_machine.setdefault(task["Machine"], set()).add(task["Tâches"])

    sorted_resources = list(
        itertools.chain.from_iterable(
            [sorted(resource_per_machine[machine]) for machine in ordered_machines]
        )
    )

    fig = px.timeline(
        gantt_df, x_start="Start", x_end="Finish", y="Tâches", color="Train"
    )
    fig.update_layout(xaxis=dict(title="Temps", tickformat="%d/%m/%y %H:%M"))
    fig.update_yaxes(categoryorder="array", categoryarray=sorted_resources[::-1])
    return fig


def visualisation_occupation(
    occupation_REC: list, occupation_FOR: list, occupation_DEP: list, x_date: list
) -> bool:
    """
    Prépare la visualisation de l'occupation des voies de chaque chantier en fonction du temps.

    Paramètres :
    -----------
    occupation_REC : list
        Occupation des voies du chantier de réception en fonction du temps.
    occupation_FOR : list
        Occupation des voies du chantier de formation en fonction du temps.
    occupation_DEP : list
        Occupation des voies du chantier de départ en fonction du temps.
    x_date : list
        Horodatage des points des listes précédentes.

    Retourne :
    ---------
    bool
        True si le graphique est construit.
    """
    # Calcul des valeurs maximales
    max_REC = max(occupation_REC)
    max_FOR = max(occupation_FOR)
    max_DEP = max(occupation_DEP)

    # Tracé des courbes
    plt.figure(figsize=(10, 5))
    plt.plot(x_date, occupation_REC, label="REC", color="#a1006b")
    plt.plot(x_date, occupation_FOR, label="FOR", color="#009aa6")
    plt.plot(x_date, occupation_DEP, label="DEP", color="#d2e100")

    # Ajout des lignes horizontales aux valeurs max
    plt.axhline(
        y=max_REC,
        color="#a1006b",
        linestyle="--",
        linewidth=2,
        label=f"Max REC ({int(max_REC)})",
    )
    plt.axhline(
        y=max_FOR,
        color="#009aa6",
        linestyle="--",
        linewidth=2,
        label=f"Max FOR ({int(max_FOR)})",
    )
    plt.axhline(
        y=max_DEP,
        color="#d2e100",
        linestyle="--",
        linewidth=2,
        label=f"Max DEP ({int(max_DEP)})",
    )

    # Étiquettes et légende
    plt.xlabel("Date")
    plt.ylabel("Nombre de voies occupées")
    plt.legend()
    plt.grid(True)

    # Appliquer le format de date "jj/mm/aaaa"
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))

    # Espacer les ticks de l'axe X (ajustable selon le nombre de points)
    plt.gca().xaxis.set_major_locator(
        mdates.DayLocator(interval=1)
    )  # Affiche une date par jour

    # Optionnel : masquer les ticks de l'axe x si on ne remplace pas par les dates
    plt.xticks(rotation=45)

    return True
