"""
module pour initier le modèle du jalon 1
"""

import gurobipy as grb
import numpy as np
from module.utils1 import (
    creation_limites_machines,
    creation_limites_chantiers,
    # read_sillon,
    # base_time,
    Machines,
    Chantiers,
)
# import pandas as pd


class Taches:
    """Contient constantes liées aux taches et à leur temporalité."""

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

    # Horaires limites de la disponibilité du chantier de formation et des machines (en minutes)
    LIMITES = np.array(
        [
            5 * 60,
            13 * 60,
            (5 * 24 + 13) * 60,
            (5 * 24 + 21) * 60,
            (6 * 24 + 13) * 60,
            (6 * 24 + 21) * 60,
            (7 * 24 + 5) * 60,
            (7 * 24 + 13) * 60,
        ]
    )


# initiation du model avec les bonnes variables et les bonnes contraintes
def init_model(
    liste_id_train_arrivee: list,
    t_a: dict,
    liste_id_train_depart: list,
    t_d: dict,
    dict_correspondances: dict,
    file: str,
    id_file,
) -> grb.Model:
    """initie le model à optimiser en mettant les variables et les contraintes"""
    model = grb.Model("SNCF JALON 1")

    t_arr, t_dep = init_variables(
        model,
        liste_id_train_arrivee,
        liste_id_train_depart,
    )

    init_contraintes(
        model,
        t_arr,
        t_a,
        liste_id_train_arrivee,
        t_dep,
        t_d,
        liste_id_train_depart,
        dict_correspondances,
        file,
        id_file,
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model, t_arr, t_dep


# initiations des variables
def init_variables(
    m: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
) -> (dict, dict):
    t_arr = variables_debut_tache_arrive(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)

    return t_arr, t_dep


def variables_debut_tache_arrive(
    model: grb.Model,
    liste_id_train_arrivee: list,
) -> dict:
    """Temps de début de la tâche m sur le train d'arrivée n, en minute, comptée à partir du lundi 8 Aout 2022 00:00"""
    t_arr = {
        (m, id_train_arr): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_ARRIVEE
        for id_train_arr in liste_id_train_arrivee
    }
    return t_arr


def variables_debut_tache_depart(
    model: grb.Model,
    liste_id_train_depart: list,
) -> dict:
    """Temps de début de la tâche m sur le train de départ n, en minute, comptée à partir du lundi 8 Aout 2022 00:00"""
    t_dep = {
        (m, id_train_dep): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_DEPART
        for id_train_dep in liste_id_train_depart
    }
    return t_dep


# initiation des contraintes
def init_contraintes(
    model: grb.Model,
    t_arr: dict,
    t_a: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    t_d: dict,
    liste_id_train_depart: list,
    dict_correspondances: dict,
    file: str,
    id_file,
) -> bool:
    contraintes_temporalite(
        model,
        t_arr,
        t_a,
        liste_id_train_arrivee,
        t_dep,
        t_d,
        liste_id_train_depart,
    )

    contraintes_machines(
        model,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
    )

    contraintes_ouvertures_machines(
        model,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
        file,
        id_file,
    )

    contraintes_ouvertures_chantiers(
        model,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
        file,
        id_file,
    )

    # delta_lim_arr, delta_lim_dep = contraintes_ouvertures(
    #     model,
    #     t_arr,
    #     liste_id_train_arrivee,
    #     t_dep,
    #     liste_id_train_depart,
    # )

    contraintes_succession(
        model,
        t_arr,
        t_dep,
        liste_id_train_depart,
        dict_correspondances,
    )

    return True


def contraintes_temporalite(
    model: grb.Model,
    t_arr: dict,
    t_a: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    t_d: dict,
    liste_id_train_depart: list,
) -> bool:
    """Contraintes de temporalité des tâches sur un même train et respect des heures de départ et d'arrivée"""
    for id_train_arr in liste_id_train_arrivee:
        model.addConstr(t_arr[(1, id_train_arr)] >= t_a[id_train_arr])
        for m in Taches.TACHES_ARRIVEE[:-1]:
            model.addConstr(
                t_arr[(m, id_train_arr)] + Taches.T_ARR[m]
                <= t_arr[(m + 1, id_train_arr)]
            )

    for id_train_dep in liste_id_train_depart:
        M_dep = Taches.TACHES_DEPART[-1]
        model.addConstr(
            t_dep[(M_dep, id_train_dep)] + Taches.T_DEP[M_dep]
            <= t_d[id_train_dep]
        )
        for m in Taches.TACHES_DEPART[:-1]:
            model.addConstr(
                t_dep[(m, id_train_dep)] + Taches.T_DEP[m]
                <= t_dep[(m + 1, id_train_dep)]
            )
    return True


def contraintes_machines(
    model: grb.Model,
    t_arr: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    liste_id_train_depart: list,
) -> (dict, dict):
    """Contrainte permettant d'avoir au plus un wagon par machine à chaque instant"""

    M_big = 100000  # Une grande constante, à ajuster en fonction de tes données
    delta_arr = {}

    for m_arr in Taches.TACHES_ARR_MACHINE:
        for id_arr_1 in liste_id_train_arrivee:
            for id_arr_2 in liste_id_train_arrivee:
                if id_arr_1 != id_arr_2:
                    delta_arr[(m_arr, id_arr_1, id_arr_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_arr_{m_arr}_{id_arr_1}_{id_arr_2}",
                    )

                    # Si delta = 1, alors id_arr_2 se termine avant id_arr_1
                    model.addConstr(
                        t_arr[(m_arr, id_arr_2)] + Taches.T_ARR[m_arr]
                        <= t_arr[(m_arr, id_arr_1)]
                        + (1 - delta_arr[(m_arr, id_arr_1, id_arr_2)]) * M_big
                    )

                    # Si delta = 0, alors id_arr_1 se termine avant id_arr_2
                    model.addConstr(
                        t_arr[(m_arr, id_arr_2)]
                        >= t_arr[(m_arr, id_arr_1)]
                        + Taches.T_ARR[m_arr]
                        - delta_arr[(m_arr, id_arr_1, id_arr_2)] * M_big
                    )

    delta_dep = {}

    for m_dep in Taches.TACHES_DEP_MACHINE:
        for id_dep_1 in liste_id_train_depart:
            for id_dep_2 in liste_id_train_depart:
                if id_dep_1 != id_dep_2:
                    delta_dep[(m_dep, id_dep_1, id_dep_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_dep_{m_dep}_{id_dep_1}_{id_dep_2}",
                    )

                    # Si delta = 1, alors id_dep_2 se termine avant id_dep_1
                    model.addConstr(
                        t_dep[(m_dep, id_dep_2)] + Taches.T_DEP[m_dep]
                        <= t_dep[(m_dep, id_dep_1)]
                        + (1 - delta_dep[(m_dep, id_dep_1, id_dep_2)]) * M_big
                    )

                    # Si delta = 0, alors id_dep_1 se termine avant id_dep_2
                    model.addConstr(
                        t_dep[(m_dep, id_dep_2)]
                        >= t_dep[(m_dep, id_dep_1)]
                        + Taches.T_DEP[m_dep]
                        - delta_dep[(m_dep, id_dep_1, id_dep_2)] * M_big
                    )

    return delta_arr, delta_dep


def contraintes_ouvertures_machines(
    model: grb.Model,
    t_arr: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    liste_id_train_depart: list,
    file: str,
    id_file: int,
) -> (dict, dict, dict):
    """Contrainte de respect des horaires d'utilisation des machines"""
    M_big = 10000000  # Une grande constante pour relacher certaines contraintes

    Limites_machines = creation_limites_machines(file, id_file)

    N_machines = {
        key: len(Limites_machines[key]) for key in Limites_machines.keys()
    }

    delta_lim_machine_DEB = {}

    if N_machines[Machines.DEB] > 0:
        for id_arr in liste_id_train_arrivee:
            delta_lim_machine_DEB[id_arr] = model.addVars(
                N_machines[Machines.DEB] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_DEB_{id_arr}",
            )  # N//2 + 1  contraintes
            # Premier cas : Avant la première limite
            model.addConstr(
                t_arr[(3, id_arr)]
                <= Limites_machines[Machines.DEB][0]
                - Taches.T_ARR[3]
                + (1 - delta_lim_machine_DEB[id_arr][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEB] // 2):
                model.addConstr(
                    t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][2*i-1]
                    - (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )
                model.addConstr(
                    t_arr[(3, id_arr)]
                    <= Limites_machines[Machines.DEB][2*i]
                    - Taches.T_ARR[3]
                    + (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )

            # Dernier cas : Après la dernière limite (
            if N_machines[Machines.DEB] % 2 == 0:
                model.addConstr(
                    t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][-1]
                    - (
                        1
                        - delta_lim_machine_DEB[id_arr][
                            N_machines[Machines.DEB] // 2
                        ]
                    )
                    * M_big
                )

            # Une seule condition peut être vraie (avant, entre ou après les limites)
            model.addConstr(
                grb.quicksum(
                    [delta_lim_machine_DEB[id_arr][i]
                     for i in range(N_machines[Machines.DEB] // 2 + 1)]
                )
                == 1
            )

    delta_lim_machine_FOR = {}

    if N_machines[Machines.FOR] > 0:
        for id_dep in liste_id_train_depart:
            delta_lim_machine_FOR[id_dep] = model.addVars(
                N_machines[Machines.FOR] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_1_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                t_dep[(1, id_dep)]
                <= Limites_machines[Machines.FOR][0]
                - Taches.T_DEP[1]
                + (1 - delta_lim_machine_FOR[id_dep][0]) * M_big
            )

            # Cas intermédiaires
            for i in range(1, N_machines[Machines.FOR] // 2):
                model.addConstr(
                    t_dep[(1, id_dep)]
                    >= Limites_machines[Machines.FOR][2*i-1]
                    - (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    t_dep[(1, id_dep)]
                    <= Limites_machines[Machines.FOR][2*i]
                    - Taches.T_DEP[1]
                    + (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.FOR] % 2 == 0:
                model.addConstr(
                    t_dep[(1, id_dep)]
                    >= Limites_machines[Machines.FOR][-1]
                    - (
                        1
                        - delta_lim_machine_FOR[id_dep][
                            N_machines[Machines.FOR] // 2
                        ]
                    )
                    * M_big
                )

            # Une seule de ces conditions peut être vraie
            model.addConstr(
                grb.quicksum(
                    [delta_lim_machine_FOR[id_dep][i]
                     for i in range(N_machines[Machines.FOR] // 2 + 1)]
                )
                == 1
            )

    delta_lim_machine_DEG = {}

    if N_machines[Machines.DEG] > 0:
        for id_dep in liste_id_train_depart:
            delta_lim_machine_DEG[id_dep] = model.addVars(
                N_machines[Machines.DEG] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_3_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                t_dep[(3, id_dep)]
                <= Limites_machines[Machines.DEG][0]
                - Taches.T_DEP[3]
                + (1 - delta_lim_machine_DEG[id_dep][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEG] // 2):
                model.addConstr(
                    t_dep[(3, id_dep)]
                    >= Limites_machines[Machines.DEG][2*i-1]
                    - (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    t_dep[(3, id_dep)]
                    <= Limites_machines[Machines.DEG][2*i]
                    - Taches.T_DEP[3]
                    + (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.DEG] % 2 == 0:
                model.addConstr(
                    t_dep[(3, id_dep)]
                    >= Limites_machines[Machines.DEG][-1]
                    - (
                        1
                        - delta_lim_machine_DEG[id_dep][
                            N_machines[Machines.DEG] // 2
                        ]
                    )
                    * M_big
                )

            # Une seule de ces conditions peut être vraie
            model.addConstr(
                grb.quicksum(
                    [delta_lim_machine_DEG[id_dep][i]
                     for i in range(N_machines[Machines.DEG] // 2 + 1)]
                )
                == 1
            )
    return (
        delta_lim_machine_DEB,
        delta_lim_machine_FOR,
        delta_lim_machine_DEG,
    )


def contraintes_ouvertures_chantiers(
    model: grb.Model,
    t_arr: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    liste_id_train_depart: list,
    file: str,
    id_file: int
) -> (dict, dict):
    M_big = 10000000  # Une grande constante pour relacher certaines contraintes

    Limites_chantiers = creation_limites_chantiers(file, id_file)

    N_chantiers = {
        key: len(Limites_chantiers[key]) for key in Limites_chantiers.keys()
    }

    delta_lim_chantier_rec = {1: {}, 2: {}, 3: {}}

    if N_chantiers[Chantiers.REC] > 0:
        for id_arr in liste_id_train_arrivee:
            for m in range(
                min(delta_lim_chantier_rec.keys()),
                max(delta_lim_chantier_rec.keys()) + 1,
            ):
                delta_lim_chantier_rec[m][id_arr] = model.addVars(
                    N_chantiers[Chantiers.REC] // 2 + 1,
                    vtype=grb.GRB.BINARY,
                    name=f"delta_REC_{m}_{id_arr}",
                )  # N//2 + 1  contraintes

                # Premier cas : Avant la première limite
                model.addConstr(
                    t_arr[(m, id_arr)]
                    <= Limites_chantiers[Chantiers.REC][0]
                    - Taches.T_ARR[m]
                    + (1 - delta_lim_chantier_rec[m][id_arr][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.REC] // 2):
                    model.addConstr(
                        t_arr[(m, id_arr)]
                        >= Limites_chantiers[Chantiers.REC][2*i-1]
                        - (1 - delta_lim_chantier_rec[m][id_arr][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        t_arr[(m, id_arr)]
                        <= Limites_chantiers[Chantiers.REC][2*i]
                        - Taches.T_ARR[m]
                        + (1 - delta_lim_chantier_rec[m][id_arr][i])
                        * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.REC] % 2 == 0:
                    model.addConstr(
                        t_arr[(m, id_arr)]
                        >= Limites_chantiers[Chantiers.REC][-1]
                        - (
                            1
                            - delta_lim_chantier_rec[m][id_arr][
                                N_chantiers[Chantiers.REC] // 2
                            ]
                        )
                        * M_big
                    )

                # Une seule condition peut être vraie (avant, entre ou après les limites)
                model.addConstr(
                    grb.quicksum(
                        [delta_lim_chantier_rec[m][id_arr][i]
                         for i in range(N_chantiers[Chantiers.REC] // 2 + 1)]
                    )
                    == 1
                )

    delta_lim_chantier_for = {1: {}, 2: {}, 3: {}}

    if N_chantiers[Chantiers.FOR] > 0:
        for id_dep in liste_id_train_depart:
            for m in range(
                min(delta_lim_chantier_for.keys()),
                max(delta_lim_chantier_for.keys()) + 1,
            ):
                delta_lim_chantier_for[m][id_dep] = model.addVars(
                    N_chantiers[Chantiers.FOR] // 2 + 1,
                    vtype=grb.GRB.BINARY,
                    name=f"delta_FOR_{m}_{id_dep}",
                )  # N//2 + 1  contraintes

                # Premier cas : Avant la première limite
                model.addConstr(
                    t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.FOR][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_for[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.FOR] // 2):
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.FOR][2*i-1]
                        - (1 - delta_lim_chantier_for[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.FOR][2*i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_for[m][id_dep][i])
                        * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.FOR] % 2 == 0:
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.FOR][-1]
                        - (
                            1
                            - delta_lim_chantier_for[m][id_dep][
                                N_chantiers[Chantiers.FOR] // 2
                            ]
                        )
                        * M_big
                    )

                # Une seule condition peut être vraie (avant, entre ou après les limites)
                model.addConstr(
                    grb.quicksum(
                        [delta_lim_chantier_for[m][id_dep][i]
                         for i in range(N_chantiers[Chantiers.FOR] // 2 + 1)]
                    )
                    == 1
                )

    delta_lim_chantier_dep = {4: {}}

    if N_chantiers[Chantiers.DEP] > 0:
        for id_dep in liste_id_train_depart:
            for m in range(
                min(delta_lim_chantier_dep.keys()),
                max(delta_lim_chantier_dep.keys()) + 1,
            ):
                delta_lim_chantier_dep[m][id_dep] = model.addVars(
                    N_chantiers[Chantiers.DEP] // 2 + 1,
                    vtype=grb.GRB.BINARY,
                    name=f"delta_DEP_{m}_{id_dep}",
                )  # N//2 + 1  contraintes

                # Premier cas : Avant la première limite
                model.addConstr(
                    t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.DEP][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_dep[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.DEP] // 2):
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.DEP][2*i-1]
                        - (1 - delta_lim_chantier_dep[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.DEP][2*i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_dep[m][id_dep][i])
                        * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.DEP] % 2 == 0:
                    model.addConstr(
                        t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.DEP][-1]
                        - (
                            1
                            - delta_lim_chantier_dep[m][id_dep][
                                N_chantiers[Chantiers.DEP] // 2
                            ]
                        )
                        * M_big
                    )

                # Une seule condition peut être vraie (avant, entre ou après les limites)
                model.addConstr(
                    grb.quicksum(
                        [delta_lim_chantier_dep[m][id_dep][i]
                         for i in range(N_chantiers[Chantiers.DEP] // 2 + 1)]
                    )
                    == 1
                )

    return (
        delta_lim_chantier_rec,
        delta_lim_chantier_for,
        delta_lim_chantier_dep,
    )


def contraintes_succession(
    model: grb.Model,
    t_arr: dict,
    t_dep: dict,
    liste_id_train_depart: list,
    dict_correspondances: dict,
) -> bool:
    """Contrainte de succession des tâches sur les trains d'arrivées et des tâches sur les trains de départ en tenant compte de la correspondance des wagons"""
    for id_dep in liste_id_train_depart:
        for id_arr in dict_correspondances[id_dep]:
            model.addConstr(
                t_dep[(1, id_dep)] >= t_arr[(3, id_arr)] + Taches.T_ARR[3]
            )
    return True
