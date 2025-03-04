import datetime
import pandas as pd
import itertools
import plotly.express as px


def GANTT(base_time, T_arr, T_dep, t_arr, t_dep, ):
    # Liste ordonnée des machines
    ORDERED_MACHINES = ["arr_1", "arr_2", "arr_3",
                        "dep_1", "dep_2", "dep_3", "dep_4"]

    # Données fournies sous forme de liste de dictionnaires
    tasks = [
        {"Train": n_arr,
         "Start": base_time + datetime.timedelta(minutes=var_arr.X),
         "Finish": base_time + datetime.timedelta(minutes=var_arr.X + T_arr[m_arr]),
         "Machine": f"arr_{m_arr}",
         "Resource": f"arr_{m_arr}"}
        for (m_arr, n_arr), var_arr in t_arr.items()
    ] + [
        {"Train": n_dep,
         "Start": base_time + datetime.timedelta(minutes=var_dep.X),
         "Finish": base_time + datetime.timedelta(minutes=var_dep.X + T_dep[m_dep]),
         "Machine": f"dep_{m_dep}",
         "Resource": f"dep_{m_dep}"}
        for (m_dep, n_dep), var_dep in t_dep.items()
    ]

    # Construction du DataFrame pour la visualisation
    gantt_df = pd.DataFrame(tasks)

    # Regroupement des ressources par machine
    resource_per_machine = {}
    for task in tasks:
        resource_per_machine.setdefault(
            task["Machine"], set()).add(task["Resource"])

    sorted_resources = list(itertools.chain.from_iterable(
        [sorted(resource_per_machine[machine]) for machine in ORDERED_MACHINES]
    ))

    fig = px.timeline(gantt_df, x_start="Start",
                      x_end="Finish", y="Resource", color="Train")
    fig.update_layout(xaxis=dict(title='Timestamp',
                      tickformat='%d/%m/%y %H:%M'))
    fig.update_yaxes(categoryorder="array",
                     categoryarray=sorted_resources[::-1])
    fig.show()
