"""
Module de gestion des opérations sur les trains utilisant Gurobi pour l'optimisation.

Ce module définit les tâches et contraintes pour la planification des opérations
sur les trains, incluant les tâches d'arrivée et de départ, ainsi que les
contraintes temporelles et de succession.

Classes :
---------
Taches : Constantes et attributs des tâches à effectuer sur les trains.

Fonctions :
-----------
init_model : Initialise le modèle Gurobi avec les contraintes de base.
"""

import gurobipy as grb
import numpy as np
from tqdm import tqdm
from itertools import product
from module.utils1 import (
    creation_limites_machines,
    creation_limites_chantiers,
    Machines,
    Chantiers,
)


class Taches:
    """
    Constantes des tâches à effectuer sur les trains et leur temporalité.

    Attributs :
    ----------
    TACHES_ARRIVEE : list[int]
        Tâches à effectuer à l'arrivée d'un train.
    TACHES_DEPART : list[int]
        Tâches à effectuer au départ d'un train.
    TACHES_ARR_MACHINE : list[int]
        Tâches d'arrivée nécessitant une machine.
    TACHES_DEP_MACHINE : list[int]
        Tâches de départ nécessitant une machine.
    T_ARR : dict[int, int]
        Durée des tâches d'arrivée (en minutes).
    T_DEP : dict[int, int]
        Durée des tâches de départ (en minutes).
    LIMITES : np.ndarray
        Horaires limites du chantier et des machines (en minutes).
    """

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


def init_model(
    liste_id_train_arrivee: list,
    t_a: dict,
    liste_id_train_depart: list,
    t_d: dict,
    dict_correspondances: dict,
    file: str,
    id_file: int,
    limites_voies: dict,
    tempsMax: int,
    tempsMin: int,
) -> tuple[grb.Model, dict, dict]:
    """
    Initialise le modèle d'optimisation avec les variables et contraintes.

    Paramètres :
    -----------
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_a : dict
        Temps d'arrivée à la gare de fret des trains.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    t_d : dict
        Temps de départ de la gare de fret des trains.
    dict_correspondances : dict
        Correspondances entre trains d'arrivée et de départ.
    file : str
        Nom du fichier de configuration.
    id_file :
        Identifiant du fichier.

    Retourne :
    ---------
    grb.Model
        Modèle d'optimisation Gurobi initialisé.
    tuple
        Variables du modèle (t_arr, t_dep).
    """
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
        limites_voies,
        tempsMax,
        tempsMin,
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model, t_arr, t_dep


def init_variables(
    m: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
) -> tuple[dict, dict]:
    """
    Initialise les variables de début des tâches pour les trains.

    Paramètres :
    -----------
    m : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    tuple[dict, dict]
        - Variables des débuts de tâches d'arrivée.
        - Variables des débuts de tâches de départ.
    """
    t_arr = variables_debut_tache_arrive(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)

    return t_arr, t_dep


def variables_debut_tache_arrive(
    model: grb.Model,
    liste_id_train_arrivee: list,
) -> dict:
    """
    Initialise les variables de début des tâches pour les trains à l'arrivée.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.

    Retourne :
    ---------
    dict
        Variables de début des tâches d'arrivée, indexées par (tâche, train).
    """
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
    """
    Initialise les variables de début des tâches pour les trains au départ.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    dict
        Variables de début des tâches de départ, indexées par (tâche, train).
    """
    t_dep = {
        (m, id_train_dep): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_DEPART
        for id_train_dep in liste_id_train_depart
    }
    return t_dep


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
    id_file: int,
    limites_voies: dict,
    tempsMax: int,
    tempsMin: int,
) -> bool:
    """
    Initialise les contraintes du modèle d'optimisation.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    t_arr : dict
        Variables de début des tâches d'arrivée.
    t_a : dict
        Durée des tâches d'arrivée.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    t_d : dict
        Durée des tâches de départ.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    dict_correspondances : dict
        Correspondances entre trains d'arrivée et de départ.
    file : str
        Nom du fichier de configuration.
    id_file : int
        Identifiant du fichier.

    Retourne :
    ---------
    bool
        Toujours True après l'initialisation des contraintes.
    """

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

    contraintes_succession(
        model,
        t_arr,
        t_dep,
        liste_id_train_depart,
        dict_correspondances,
    )

    contraintes_nombre_voies(
        model,
        t_arr,
        t_dep,
        liste_id_train_arrivee,
        liste_id_train_depart,
        limites_voies,
        tempsMax,
        tempsMin
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
    """
    Ajoute les contraintes de temporalité des tâches sur un même train,
    ainsi que le respect des heures de départ et d'arrivée.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    t_arr : dict
        Variables de début des tâches d'arrivée.
    t_a : dict
        Durée des tâches d'arrivée.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    t_d : dict
        Durée des tâches de départ.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    bool
        Toujours True après l'ajout des contraintes de temporalité.
    """
    for id_train_arr in tqdm(liste_id_train_arrivee, "Contrainte assurant la succession des tâches sur les trains d'arrivée"):
        model.addConstr(15*t_arr[(1, id_train_arr)] >= t_a[id_train_arr])
        for m in Taches.TACHES_ARRIVEE[:-1]:
            model.addConstr(
                15*t_arr[(m, id_train_arr)] + Taches.T_ARR[m]
                <= 15*t_arr[(m + 1, id_train_arr)]
            )

    for id_train_dep in tqdm(liste_id_train_depart, "Contrainte assurant la succession des tâches sur les trains de départ"):
        M_dep = Taches.TACHES_DEPART[-1]
        model.addConstr(
            15*t_dep[(M_dep, id_train_dep)] + Taches.T_DEP[M_dep]
            <= t_d[id_train_dep]
        )
        for m in Taches.TACHES_DEPART[:-1]:
            model.addConstr(
                15*t_dep[(m, id_train_dep)] + Taches.T_DEP[m]
                <= 15*t_dep[(m + 1, id_train_dep)]
            )
    return True


def contraintes_machines(
    model: grb.Model,
    t_arr: dict,
    liste_id_train_arrivee: list,
    t_dep: dict,
    liste_id_train_depart: list,
) -> tuple[dict, dict]:
    """
    Ajoute des contraintes pour assurer qu'il n'y a qu'un seul wagon par machine
    à chaque instant, en gérant les interactions entre les trains.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    t_arr : dict
        Variables de début des tâches d'arrivée.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    tuple[dict, dict]
        - `delta_arr` : Variables binaires pour les trains à l'arrivée.
        - `delta_dep` : Variables binaires pour les trains au départ.
    """

    M_big = 100000  # Une grande constante, à ajuster en fonction de tes données
    delta_arr = {}

    for m_arr in Taches.TACHES_ARR_MACHINE:
        for id_arr_1 in tqdm(liste_id_train_arrivee, "Contrainte assurant qu'il n'y a qu'un train niveau de la machine DEB"):
            for id_arr_2 in liste_id_train_arrivee:
                if id_arr_1 != id_arr_2:
                    delta_arr[(m_arr, id_arr_1, id_arr_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_arr_{m_arr}_{id_arr_1}_{id_arr_2}",
                    )

                    # Si delta = 1, alors id_arr_2 se termine avant id_arr_1
                    model.addConstr(
                        15*t_arr[(m_arr, id_arr_2)] + Taches.T_ARR[m_arr]
                        <= 15*t_arr[(m_arr, id_arr_1)]
                        + (1 - delta_arr[(m_arr, id_arr_1, id_arr_2)]) * M_big
                    )

                    # Si delta = 0, alors id_arr_1 se termine avant id_arr_2
                    model.addConstr(
                        15*t_arr[(m_arr, id_arr_2)]
                        >= 15*t_arr[(m_arr, id_arr_1)]
                        + Taches.T_ARR[m_arr]
                        - delta_arr[(m_arr, id_arr_1, id_arr_2)] * M_big
                    )

    delta_dep = {}

    for m_dep in tqdm(Taches.TACHES_DEP_MACHINE, "Contrainte assurant qu'il n'y a qu'un train niveau des machines FOR et DEG"):
        for id_dep_1 in liste_id_train_depart:
            for id_dep_2 in liste_id_train_depart:
                if id_dep_1 != id_dep_2:
                    delta_dep[(m_dep, id_dep_1, id_dep_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_dep_{m_dep}_{id_dep_1}_{id_dep_2}",
                    )

                    # Si delta = 1, alors id_dep_2 se termine avant id_dep_1
                    model.addConstr(
                        15*t_dep[(m_dep, id_dep_2)] + Taches.T_DEP[m_dep]
                        <= 15*t_dep[(m_dep, id_dep_1)]
                        + (1 - delta_dep[(m_dep, id_dep_1, id_dep_2)]) * M_big
                    )

                    # Si delta = 0, alors id_dep_1 se termine avant id_dep_2
                    model.addConstr(
                        15*t_dep[(m_dep, id_dep_2)]
                        >= 15*t_dep[(m_dep, id_dep_1)]
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
) -> tuple[dict, dict, dict]:
    """
    Ajoute des contraintes pour respecter les horaires d'utilisation des machines
    et garantir qu'un seul train utilise une machine à la fois.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    t_arr : dict
        Variables de début des tâches d'arrivée.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    file : str
        Nom du fichier de configuration.
    id_file : int
        Identifiant du fichier.

    Retourne :
    ---------
    tuple[dict, dict, dict]
        - `delta_lim_machine_DEB` : Contraintes de limites pour les machines de type DEB.
        - `delta_lim_machine_FOR` : Contraintes de limites pour les machines de type FOR.
        - `delta_lim_machine_DEG` : Contraintes de limites pour les machines de type DEG.
    """
    M_big = 10000000  # Une grande constante pour relacher certaines contraintes

    Limites_machines = creation_limites_machines(file, id_file)

    N_machines = {
        key: len(Limites_machines[key]) for key in Limites_machines.keys()
    }

    delta_lim_machine_DEB = {}

    if N_machines[Machines.DEB] > 0:
        for id_arr in tqdm(liste_id_train_arrivee, "Contrainte de fermeture de la machine DEB"):
            delta_lim_machine_DEB[id_arr] = model.addVars(
                N_machines[Machines.DEB] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_DEB_{id_arr}",
            )  # N//2 + 1  contraintes
            # Premier cas : Avant la première limite
            model.addConstr(
                15*t_arr[(3, id_arr)]
                <= Limites_machines[Machines.DEB][0]
                - Taches.T_ARR[3]
                + (1 - delta_lim_machine_DEB[id_arr][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEB] // 2):
                model.addConstr(
                    15*t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][2 * i - 1]
                    - (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )
                model.addConstr(
                    15*t_arr[(3, id_arr)]
                    <= Limites_machines[Machines.DEB][2 * i]
                    - Taches.T_ARR[3]
                    + (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )

            # Dernier cas : Après la dernière limite (
            if N_machines[Machines.DEB] % 2 == 0:
                model.addConstr(
                    15*t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][-1]
                    - (1 - delta_lim_machine_DEB[id_arr]
                       [N_machines[Machines.DEB] // 2]) * M_big
                )

            # Une seule condition peut être vraie (avant, entre ou après les limites)
            model.addConstr(
                grb.quicksum(
                    [
                        delta_lim_machine_DEB[id_arr][i]
                        for i in range(N_machines[Machines.DEB] // 2 + 1)
                    ]
                )
                == 1
            )

    delta_lim_machine_FOR = {}

    if N_machines[Machines.FOR] > 0:
        for id_dep in tqdm(liste_id_train_depart, "Contrainte de fermeture de la machine FOR"):
            delta_lim_machine_FOR[id_dep] = model.addVars(
                N_machines[Machines.FOR] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_1_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                15*t_dep[(1, id_dep)]
                <= Limites_machines[Machines.FOR][0]
                - Taches.T_DEP[1]
                + (1 - delta_lim_machine_FOR[id_dep][0]) * M_big
            )

            # Cas intermédiaires
            for i in range(1, N_machines[Machines.FOR] // 2):
                model.addConstr(
                    15*t_dep[(1, id_dep)]
                    >= Limites_machines[Machines.FOR][2 * i - 1]
                    - (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    15*t_dep[(1, id_dep)]
                    <= Limites_machines[Machines.FOR][2 * i]
                    - Taches.T_DEP[1]
                    + (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.FOR] % 2 == 0:
                model.addConstr(
                    15*t_dep[(1, id_dep)]
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
                    [
                        delta_lim_machine_FOR[id_dep][i]
                        for i in range(N_machines[Machines.FOR] // 2 + 1)
                    ]
                )
                == 1
            )

    delta_lim_machine_DEG = {}

    if N_machines[Machines.DEG] > 0:
        for id_dep in tqdm(liste_id_train_depart, "Contrainte de fermeture de la machine DEG"):
            delta_lim_machine_DEG[id_dep] = model.addVars(
                N_machines[Machines.DEG] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_3_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                15*t_dep[(3, id_dep)]
                <= Limites_machines[Machines.DEG][0]
                - Taches.T_DEP[3]
                + (1 - delta_lim_machine_DEG[id_dep][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEG] // 2):
                model.addConstr(
                    15*t_dep[(3, id_dep)]
                    >= Limites_machines[Machines.DEG][2 * i - 1]
                    - (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    15*t_dep[(3, id_dep)]
                    <= Limites_machines[Machines.DEG][2 * i]
                    - Taches.T_DEP[3]
                    + (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.DEG] % 2 == 0:
                model.addConstr(
                    15*t_dep[(3, id_dep)]
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
                    [
                        delta_lim_machine_DEG[id_dep][i]
                        for i in range(N_machines[Machines.DEG] // 2 + 1)
                    ]
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
    id_file: int,
) -> tuple[dict, dict, dict]:
    """
    Ajoute des contraintes pour respecter les horaires d'ouverture des chantiers
    et garantir que chaque train respecte les limites d'ouverture des différents chantiers.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    t_arr : dict
        Variables de début des tâches d'arrivée.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    file : str
        Nom du fichier de configuration.
    id_file : int
        Identifiant du fichier.

    Retourne :
    ---------
    tuple[dict, dict, dict]
        - `delta_lim_chantier_rec` : Contraintes des limites d'ouverture pour les chantiers de type REC.
        - `delta_lim_chantier_for` : Contraintes des limites d'ouverture pour les chantiers de type FOR.
        - `delta_lim_chantier_dep` : Contraintes des limites d'ouverture pour les chantiers de type DEP.
    """
    M_big = 10000000  # Une grande constante pour relacher certaines contraintes

    Limites_chantiers = creation_limites_chantiers(file, id_file)

    N_chantiers = {
        key: len(Limites_chantiers[key]) for key in Limites_chantiers.keys()
    }

    delta_lim_chantier_rec = {1: {}, 2: {}, 3: {}}

    if N_chantiers[Chantiers.REC] > 0:
        for id_arr in tqdm(liste_id_train_arrivee, "Contrainte de fermeture du Chantier REC"):
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
                    15*t_arr[(m, id_arr)]
                    <= Limites_chantiers[Chantiers.REC][0]
                    - Taches.T_ARR[m]
                    + (1 - delta_lim_chantier_rec[m][id_arr][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.REC] // 2):
                    model.addConstr(
                        15*t_arr[(m, id_arr)]
                        >= Limites_chantiers[Chantiers.REC][2 * i - 1]
                        - (1 - delta_lim_chantier_rec[m][id_arr][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15*t_arr[(m, id_arr)]
                        <= Limites_chantiers[Chantiers.REC][2 * i]
                        - Taches.T_ARR[m]
                        + (1 - delta_lim_chantier_rec[m][id_arr][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.REC] % 2 == 0:
                    model.addConstr(
                        15*t_arr[(m, id_arr)]
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
                        [
                            delta_lim_chantier_rec[m][id_arr][i]
                            for i in range(N_chantiers[Chantiers.REC] // 2 + 1)
                        ]
                    )
                    == 1
                )

    delta_lim_chantier_for = {1: {}, 2: {}, 3: {}}

    if N_chantiers[Chantiers.FOR] > 0:
        for id_dep in tqdm(liste_id_train_depart, "Contrainte de fermeture du Chantier FOR"):
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
                    15*t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.FOR][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_for[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.FOR] // 2):
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.FOR][2 * i - 1]
                        - (1 - delta_lim_chantier_for[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.FOR][2 * i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_for[m][id_dep][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.FOR] % 2 == 0:
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
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
                        [
                            delta_lim_chantier_for[m][id_dep][i]
                            for i in range(N_chantiers[Chantiers.FOR] // 2 + 1)
                        ]
                    )
                    == 1
                )

    delta_lim_chantier_dep = {4: {}}

    if N_chantiers[Chantiers.DEP] > 0:
        for id_dep in tqdm(liste_id_train_depart, "Contrainte de fermeture du Chantier DEG"):
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
                    15*t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.DEP][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_dep[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.DEP] // 2):
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.DEP][2 * i - 1]
                        - (1 - delta_lim_chantier_dep[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.DEP][2 * i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_dep[m][id_dep][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.DEP] % 2 == 0:
                    model.addConstr(
                        15*t_dep[(m, id_dep)]
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
                        [
                            delta_lim_chantier_dep[m][id_dep][i]
                            for i in range(N_chantiers[Chantiers.DEP] // 2 + 1)
                        ]
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
    """
    Ajoute des contraintes de succession entre les tâches d'arrivée et de départ
    des trains, en tenant compte des correspondances de wagons.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour ajouter les contraintes.

    t_arr : dict
        Temps de début des tâches d'arrivée.

    t_dep : dict
        Temps de début des tâches de départ.

    liste_id_train_depart : list
        Identifiants des trains de départ.

    dict_correspondances : dict
        Correspondances entre trains de départ et d'arrivée.

    Retourne :
    ----------
    bool
        True si les contraintes sont ajoutées.
    """
    for id_dep in tqdm(liste_id_train_depart, "Contrainte assurant la succession des tâches entre les chantiers de REC et FOR"):
        for id_arr in dict_correspondances[id_dep]:
            model.addConstr(
                15*t_dep[(1, id_dep)] >= 15 *
                t_arr[(3, id_arr)] + Taches.T_ARR[3]
            )
    return True


def contraintes_nombre_voies(
    model: grb.Model,
    t_arr: dict,
    t_dep: dict,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    limites_voies: dict,
    tempsMax: int,
    tempsMin: int = 0,
) -> bool:

    Mbig = 1000000
    eps = 0.1

    # Créer des variables binaires : est-ce que le train est présent ?
    before_upper_bound = {
        Chantiers.REC: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"before_ub_REC_{id_train}_{t}")
                        for id_train in liste_id_train_arrivee for t in range(tempsMin, tempsMax+1)},
        Chantiers.FOR: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"before_ub_FOR_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)},
        Chantiers.DEP: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"before_ub_DEP_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)}
    }

    after_lower_bound = {
        Chantiers.REC: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"after_lb_REC_{id_train}_{t}")
                        for id_train in liste_id_train_arrivee for t in range(tempsMin, tempsMax+1)},
        Chantiers.FOR: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"after_lb_FOR_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)},
        Chantiers.DEP: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"after_lb_DEP_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)}
    }

    is_present = {
        Chantiers.REC: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"is_present_REC_{id_train}_{t}")
                        for id_train in liste_id_train_arrivee for t in range(tempsMin, tempsMax+1)},
        Chantiers.FOR: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"is_present_FOR_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)},
        Chantiers.DEP: {(id_train, t): model.addVar(vtype=grb.GRB.BINARY, name=f"is_present_DEP_{id_train}_{t}")
                        for id_train in liste_id_train_depart for t in range(tempsMin, tempsMax+1)}
    }

    for id_train in liste_id_train_arrivee:
        for t in range(tempsMin, tempsMax+1):  # Parcours du temps
            # Si le train est présent, t_start <= t <= t_end
            # is_present => t_arr[(1, id_train)] <= t
            model.addConstr(
                t >= t_arr[(1, id_train)] - Mbig * (1 -
                                                    after_lower_bound[Chantiers.REC][(id_train, t)]),
                name=f"after_lower_bound_REC_{id_train}_{t}"
            )
            model.addConstr(t <= t_arr[(1, id_train)] - eps + Mbig *
                            after_lower_bound[Chantiers.REC][(id_train, t)], name="bigM_constr_REC_after_lb")

            model.addConstr(
                t <= t_arr[(3, id_train)] + Taches.T_ARR[3] + Mbig *
                (1 - before_upper_bound[Chantiers.REC][(id_train, t)]),
                name=f"before_upper_bound_REC_{id_train}_{t}"
            )
            model.addConstr(t >= t_arr[(3, id_train)] + Taches.T_ARR[3] + eps - Mbig *
                            before_upper_bound[Chantiers.REC][(id_train, t)], name="bigM_constr_REC_before_ub")

            model.addGenConstrAnd(is_present[Chantiers.REC][(id_train, t)], [after_lower_bound[Chantiers.REC][(
                id_train, t)], before_upper_bound[Chantiers.REC][(id_train, t)]], "andconstr_REC")

    for id_train in liste_id_train_depart:
        for t in range(tempsMin, tempsMax+1):  # Parcours du temps
            # Si le train est présent, t_start <= t <= t_end
            model.addConstr(
                t >= t_dep[(1, id_train)] - Mbig * (1 -
                                                    after_lower_bound[Chantiers.FOR][(id_train, t)]),
                name=f"after_lower_bound_FOR_{id_train}_{t}"
            )
            model.addConstr(t <= t_dep[(1, id_train)] - eps + Mbig *
                            after_lower_bound[Chantiers.FOR][(id_train, t)], name="bigM_constr_FOR_after_lb")

            model.addConstr(
                t <= t_dep[(3, id_train)] + Taches.T_DEP[3] + Mbig *
                (1 - before_upper_bound[Chantiers.FOR][(id_train, t)]),
                name=f"before_upper_bound_FOR_{id_train}_{t}"
            )
            model.addConstr(t >= t_dep[(3, id_train)] + Taches.T_DEP[3] + eps - Mbig *
                            before_upper_bound[Chantiers.FOR][(id_train, t)], name="bigM_constr_FOR_before_ub")

            model.addGenConstrAnd(is_present[Chantiers.FOR][(id_train, t)], [after_lower_bound[Chantiers.FOR][(
                id_train, t)], before_upper_bound[Chantiers.FOR][(id_train, t)]], "andconstr_FOR")

            model.addConstr(
                t >= t_dep[(4, id_train)] - Mbig * (1 -
                                                    after_lower_bound[Chantiers.DEP][(id_train, t)]),
                name=f"after_lower_bound_DEP_{id_train}_{t}"
            )
            model.addConstr(t <= t_dep[(4, id_train)] - eps + Mbig *
                            after_lower_bound[Chantiers.DEP][(id_train, t)], name="bigM_constr_DEP_after_lb")

            model.addConstr(
                t <= t_dep[(4, id_train)] + Taches.T_DEP[4] + Mbig *
                (1 - before_upper_bound[Chantiers.DEP][(id_train, t)]),
                name=f"before_upper_bound_DEP_{id_train}_{t}"
            )
            model.addConstr(t >= t_dep[(4, id_train)] + Taches.T_DEP[4] + eps - Mbig *
                            before_upper_bound[Chantiers.DEP][(id_train, t)], name="bigM_constr_DEP_before_ub")

            model.addGenConstrAnd(is_present[Chantiers.DEP][(id_train, t)], [after_lower_bound[Chantiers.DEP][(
                id_train, t)], before_upper_bound[Chantiers.DEP][(id_train, t)]], "andconstr_DEP")

    for t in tqdm(range(tempsMin, tempsMax + 1), "Contrainte relative au nombre de voies des chantiers"):
        model.addConstr(
            grb.quicksum([is_present[Chantiers.REC][(id_train, t)]
                         for id_train in liste_id_train_arrivee])
            <= limites_voies[Chantiers.REC]
        )

        model.addConstr(
            grb.quicksum([is_present[Chantiers.FOR][(id_train, t)]
                         for id_train in liste_id_train_depart])
            <= limites_voies[Chantiers.FOR]
        )
        model.addConstr(
            grb.quicksum([is_present[Chantiers.DEP][(id_train, t)]
                         for id_train in liste_id_train_depart])
            <= limites_voies[Chantiers.DEP]
        )

    return True
