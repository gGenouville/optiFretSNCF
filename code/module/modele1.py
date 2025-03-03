"""
module pour initier le modèle du jalon 1
"""

import gurobipy as grb
import numpy as np


class Taches:
    """Contient constantes liées aux taches et à leur temporalité."""

    # définition des taches
    TACHES_ARRIVEE = [1, 2, 3]
    TACHES_DEPART = [1, 2, 3, 4]

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
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model


# initiations des variables
def init_variables(
    m:grb.Model,
    liste_id_train_arrivee:list,
    liste_id_train_depart:list,
)->(dict,dict):
    t_arr = variables_debut_tache_arrive(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)

    return t_arr, t_dep


def variables_debut_tache_arrive(
    model:grb.Model,
    liste_id_train_arrivee:list,
)->dict:
    """Temps de début de la tâche m sur le train d'arrivée n, en minute, comptée à partir du lundi 8 Aout 2022 00:00"""
    t_arr = {
        (m, id_train_arr): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_ARRIVEE
        for id_train_arr in liste_id_train_arrivee
    }
    return t_arr


def variables_debut_tache_depart(
    model:grb.Model,
    liste_id_train_depart:list,
)->dict:
    """Temps de début de la tâche m sur le train de départ n, en minute, comptée à partir du lundi 8 Aout 2022 00:00"""
    t_dep = {
        (m, id_train_dep): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_DEPART
        for id_train_dep in liste_id_train_depart
    }
    return t_dep


# initiation des contraintes
def init_contraintes(
    model:grb.Model,
    t_arr:dict,
    t_a:dict,
    liste_id_train_arrivee:list,
    t_dep:dict,
    t_d:dict,
    liste_id_train_depart:list,
    dict_correspondances:dict,
)->(dict, dict, dict, dict):
    contraintes_temporalite(
        model,
        t_arr,
        t_a,
        liste_id_train_arrivee,
        t_dep,
        t_d,
        liste_id_train_depart,
    )

    delta_arr, delta_dep = contraintes_machines(
        model,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
    )

    delta_lim_arr, delta_lim_dep = contraintes_ouvertures(
        model,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
    )

    contraintes_succession(
        model,
        t_arr,
        t_dep,
        liste_id_train_depart,
        dict_correspondances,
    )

    return delta_arr, delta_dep, delta_lim_arr, delta_lim_dep


def contraintes_temporalite(
    model:grb.Model,
    t_arr:dict,
    t_a:dict,
    liste_id_train_arrivee:list,
    t_dep:dict,
    t_d:dict,
    liste_id_train_depart:list,
)->bool:
    """Contraintes de temporalité des tâches sur un même train et respect des heures de départ et d'arrivée"""
    for id_train_arr in liste_id_train_arrivee:
        model.addConstr(t_arr[(1, id_train_arr)] >= t_a[id_train_arr])
        for m in Taches.TACHES_ARRIVEE[:-1]:
            model.addConstr(t_arr[(m, id_train_arr)] + Taches.T_ARR[m] <= t_arr[(m + 1, id_train_arr)])

    for id_train_dep in liste_id_train_depart:
        M_dep = Taches.TACHES_DEPART[-1]
        model.addConstr(t_dep[(M_dep, id_train_dep)] + Taches.T_DEP[M_dep] <= t_d[id_train_dep])
        for m in Taches.TACHES_DEPART[:-1]:
            model.addConstr(t_dep[(m, id_train_dep)] + Taches.T_DEP[m] <= t_dep[(m + 1, id_train_dep)])
    return True


def contraintes_machines(
    model:grb.Model,
    t_arr:dict,
    liste_id_train_arrivee:list,
    t_dep:dict,
    liste_id_train_depart:list,
)->(dict,dict):
    """Contrainte permettant d'avoir au plus un wagon par machine à chaque instant"""

    M_big = 100000  # Une grande constante, à ajuster en fonction de tes données
    delta_arr = {}

    for id_arr_1 in liste_id_train_arrivee:
        for id_arr_2 in liste_id_train_arrivee:
            if id_arr_1 != id_arr_2:
                delta_arr[(id_arr_1, id_arr_2)] = model.addVar(
                    vtype=grb.GRB.BINARY, name=f"delta_arr_{id_arr_1}_{id_arr_2}"
                )

                # Si delta = 1, alors id_arr_2 se termine avant id_arr_1
                model.addConstr(
                    t_arr[(3, id_arr_2)] + Taches.T_ARR[3]
                    <= t_arr[(3, id_arr_1)] + (1 - delta_arr[(id_arr_1, id_arr_2)]) * M_big
                )

                # Si delta = 0, alors id_arr_1 se termine avant id_arr_2
                model.addConstr(
                    t_arr[(3, id_arr_2)]
                    >= t_arr[(3, id_arr_1)] + Taches.T_ARR[3] - delta_arr[(id_arr_1, id_arr_2)] * M_big
                )

    delta_dep = {}

    for m_dep in [1, 3]:
        for id_dep_1 in liste_id_train_depart:
            for id_dep_2 in liste_id_train_depart:
                if id_dep_1 != id_dep_2:
                    delta_dep[(m_dep, id_dep_1, id_dep_2)] = model.addVar(
                        vtype=grb.GRB.BINARY, name=f"delta_dep_{m_dep}_{id_dep_1}_{id_dep_2}"
                    )

                    # Si delta = 1, alors id_dep_2 se termine avant id_dep_1
                    model.addConstr(
                        t_dep[(m_dep, id_dep_2)] + Taches.T_DEP[m_dep]
                        <= t_dep[(m_dep, id_dep_1)] + (1 - delta_dep[(m_dep, id_dep_1, id_dep_2)]) * M_big
                    )

                    # Si delta = 0, alors id_dep_1 se termine avant id_dep_2
                    model.addConstr(
                        t_dep[(m_dep, id_dep_2)]
                        >= t_dep[(m_dep, id_dep_1)]
                        + Taches.T_DEP[m_dep]
                        - delta_dep[(m_dep, id_dep_1, id_dep_2)] * M_big
                    )

    return delta_arr, delta_dep


def contraintes_ouvertures(
    model:grb.Model,
    t_arr:dict,
    liste_id_train_arrivee:list,
    t_dep:dict,
    liste_id_train_depart:list,
)->(dict,dict):
    """Contrainte de respect des horaires d'ouvertures des voies et d'utilisation des machines"""
    M_big = 100000  # Une grande constante, à ajuster en fonction de tes données

    delta_lim_arr = {}

    for id_arr in liste_id_train_arrivee:
        delta_lim_arr[id_arr] = model.addVars(
            5, vtype=grb.GRB.BINARY, name=f"delta_arr_{id_arr}"
        )  # 5 cas possibles

        # Cas 1 : Avant la première limite
        model.addConstr(
            t_arr[(3, id_arr)] <= Taches.LIMITES[0] - Taches.T_ARR[3] + (1 - delta_lim_arr[id_arr][0]) * M_big
        )

        # Cas 2 : Entre LIMITES[1] et LIMITES[2]
        model.addConstr(
            t_arr[(3, id_arr)] >= Taches.LIMITES[1] - delta_lim_arr[id_arr][1] * M_big
        )  # Limite inf
        model.addConstr(
            t_arr[(3, id_arr)] <= Taches.LIMITES[2] - Taches.T_ARR[3] + (1 - delta_lim_arr[id_arr][1]) * M_big
        )  # Limite sup

        # Cas 3 : Entre LIMITES[3] et LIMITES[4]
        model.addConstr(
            t_arr[(3, id_arr)] >= Taches.LIMITES[3] - delta_lim_arr[id_arr][2] * M_big
        )  # Limite inf
        model.addConstr(
            t_arr[(3, id_arr)] <= Taches.LIMITES[4] - Taches.T_ARR[3] + (1 - delta_lim_arr[id_arr][2]) * M_big
        )  # Limite sup

        # Cas 4 : Entre LIMITES[5] et LIMITES[6]
        model.addConstr(
            t_arr[(3, id_arr)] >= Taches.LIMITES[5] - delta_lim_arr[id_arr][3] * M_big
        )  # Limite inf
        model.addConstr(
            t_arr[(3, id_arr)] <= Taches.LIMITES[6] - Taches.T_ARR[3] + (1 - delta_lim_arr[id_arr][3]) * M_big
        )  # Limite sup

        # Cas 5 : Après la dernière limite
        model.addConstr(t_arr[(3, id_arr)] >= Taches.LIMITES[7] - delta_lim_arr[id_arr][4] * M_big)

        # Une seule de ces conditions peut être vraie
        model.addConstr(
            delta_lim_arr[id_arr][0]
            + delta_lim_arr[id_arr][1]
            + delta_lim_arr[id_arr][2]
            + delta_lim_arr[id_arr][3]
            + delta_lim_arr[id_arr][4]
            == 1
        )

    delta_lim_dep = {}

    for m_dep in [1, 2, 3]:
        for id_dep in liste_id_train_depart:
            delta_lim_dep[(m_dep, id_dep)] = model.addVars(
                5, vtype=grb.GRB.BINARY, name=f"delta_dep_{id_dep}"
            )  # 5 cas possibles

            # Cas 1 : Avant la première limite
            model.addConstr(
                t_dep[(m_dep, id_dep)]
                <= Taches.LIMITES[0] - Taches.T_DEP[m_dep] + (1 - delta_lim_dep[(m_dep, id_dep)][0]) * M_big
            )

            # Cas 2 : Entre LIMITES[1] et LIMITES[2]
            model.addConstr(
                t_dep[(m_dep, id_dep)] >= Taches.LIMITES[1] - delta_lim_dep[(m_dep, id_dep)][1] * M_big
            )  # Limite inf
            model.addConstr(
                t_dep[(m_dep, id_dep)]
                <= Taches.LIMITES[2] - Taches.T_DEP[m_dep] + (1 - delta_lim_dep[(m_dep, id_dep)][1]) * M_big
            )  # Limite sup

            # Cas 3 : Entre LIMITES[3] et LIMITES[4]
            model.addConstr(
                t_dep[(m_dep, id_dep)] >= Taches.LIMITES[3] - delta_lim_dep[(m_dep, id_dep)][2] * M_big
            )  # Limite inf
            model.addConstr(
                t_dep[(m_dep, id_dep)]
                <= Taches.LIMITES[4] - Taches.T_DEP[m_dep] + (1 - delta_lim_dep[(m_dep, id_dep)][2]) * M_big
            )  # Limite sup

            # Cas 4 : Entre LIMITES[5] et LIMITES[6]
            model.addConstr(
                t_dep[(m_dep, id_dep)] >= Taches.LIMITES[5] - delta_lim_dep[(m_dep, id_dep)][3] * M_big
            )  # Limite inf
            model.addConstr(
                t_dep[(m_dep, id_dep)]
                <= Taches.LIMITES[6] - Taches.T_DEP[m_dep] + (1 - delta_lim_dep[(m_dep, id_dep)][3]) * M_big
            )  # Limite sup

            # Cas 5 : Après la dernière limite
            model.addConstr(
                t_dep[(m_dep, id_dep)] >= Taches.LIMITES[7] - delta_lim_dep[(m_dep, id_dep)][4] * M_big
            )

            # Une seule de ces conditions peut être vraie
            model.addConstr(
                delta_lim_dep[(m_dep, id_dep)][0]
                + delta_lim_dep[(m_dep, id_dep)][1]
                + delta_lim_dep[(m_dep, id_dep)][2]
                + delta_lim_dep[(m_dep, id_dep)][3]
                + delta_lim_dep[(m_dep, id_dep)][4]
                == 1
            )
    return delta_lim_arr, delta_lim_dep


def contraintes_succession(
    model:grb.Model,
    t_arr:dict,
    t_dep:dict,
    liste_id_train_depart:list,
    dict_correspondances:dict,
)->bool:
    """Contrainte de succession des tâches sur les trains d'arrivées et des tâches sur les trains de départ en tenant compte de la correspondance des wagons"""
    for id_dep in liste_id_train_depart:
        for id_arr in dict_correspondances[id_dep]:
            model.addConstr(t_dep[(1, id_dep)] >= t_arr[(3, id_arr)] + Taches.T_ARR[3])
    return True
