"""
Sous-module de `modele2` dédié à la mise en place des contraintes.

Ce module définit les contraintes pour la planification des opérations
sur les trains.

Fonctions :
-----------
init_contraintes : Initialise les contraintes du modèle d'optimisation.
contraintes_temporalite : Ajoute les contraintes de temporalité des tâches.
contraintes_machines : Ajoute les contraintes d'exclusion pour les machines.
contraintes_ouvertures_machines : Ajoute les contraintes
        pour respecter les horaires d'utilisation des machines.
contraintes_ouvertures_chantiers : Ajoute les contraintes
        pour respecter les horaires d'ouverture des chantiers.
contraintes_succession : Ajoute des contraintes de succession entre les tâches
    d'arrivée et de départ des trains, en tenant compte des correspondances de wagons.
contraintes_nombre_voies : Ajoute des contraintes limitant
    le nombre de trains présents sur un même chantier.
contraintes_premier_wagon : Ajoute les contraintes définissant le
    temps du premier débranchement de wagon du train de départ.
"""

import gurobipy as grb
from tqdm import tqdm

from module.utils2 import (
    Chantiers,
    Machines,
    Taches,
    creation_limites_chantiers,
    creation_limites_machines,
)


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
    is_present: dict,
    premier_wagon: dict,
    temps_max: int,
    temps_min: int,
    nombre_roulements,
    nombre_cycles_agents,
    nombre_agents,
    max_agents_sur_roulement,
    equip,
    h_deb,
    who_arr,
    who_dep,
    comp_arr,
    comp_dep,
    nb_cycle_jour,
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
        Temps d'arrivée des trains en gare.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    t_d : dict
        Temps de départ des trains.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    dict_correspondances : dict
        Correspondances entre trains d'arrivée et de départ.
    file : str
        Nom du fichier de configuration.
    id_file : int
        Identifiant du fichier.
    limites_voies : dict
        Nombre de voies utilisables par chantier.
    is_present : dict
        Présence ou non du train id_train sur un chantier.
    premier_wagon : dict
        Variables de temps du début de la première tâche de débranchement
        sur les trains d'arrivée contenant des wagons du train de départ
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

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
        t_a,
        t_d,
        liste_id_train_arrivee,
        liste_id_train_depart,
        limites_voies,
        is_present,
        premier_wagon,
        temps_max,
        temps_min,
    )

    contraintes_premier_wagon(
        model, t_arr, dict_correspondances, liste_id_train_depart, premier_wagon
    )

    contrainte_nombre_max_agents(
        model,
        nombre_roulements,
        nombre_cycles_agents,
        nombre_agents,
        max_agents_sur_roulement,
        nb_cycle_jour,
    )

    unicite_roulement_et_cycle(
       model,
       equip,
       nombre_cycles_agents,
       liste_id_train_arrivee,
       liste_id_train_depart,
       who_arr,
       who_dep,
       h_deb,
    )

    non_saturation_personnel(
        model,
        nombre_roulements,
        nombre_cycles_agents,
        h_deb,
        who_arr,
        who_dep,
        liste_id_train_arrivee,
        liste_id_train_depart,
        comp_arr,
        comp_dep,
        nombre_agents,
    )

    contrainte_cohérence_who_t(
        model,
        equip,
        liste_id_train_arrivee,
        liste_id_train_depart,
        nombre_cycles_agents,
        who_arr,
        who_dep,
        h_deb,
        t_arr,
        t_dep,
    )
    contrainte_unicite_who_cycle(
        model,
        equip,
        liste_id_train_arrivee,
        liste_id_train_depart,
        nombre_cycles_agents,
        who_arr,
        who_dep,
        h_deb,
        t_arr,
        t_dep,
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
        Temps d'arrivée à la gare de fret des trains.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    t_dep : dict
        Variables de début des tâches de départ.
    t_d : dict
        Temps de départ de la gare de fret des trains.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    bool
        Toujours True après l'ajout des contraintes de temporalité.
    """
    for id_train_arr in tqdm(
        liste_id_train_arrivee,
        "Contrainte assurant la succession des tâches sur les trains d'arrivée",
    ):
        model.addConstr(15 * t_arr[(1, id_train_arr)] >= t_a[id_train_arr])
        for m in Taches.TACHES_ARRIVEE[:-1]:
            model.addConstr(
                15 * t_arr[(m, id_train_arr)] + Taches.T_ARR[m]
                <= 15 * t_arr[(m + 1, id_train_arr)]
            )

    for id_train_dep in tqdm(
        liste_id_train_depart,
        "Contrainte assurant la succession des tâches sur les trains de départ",
    ):
        m_dep = Taches.TACHES_DEPART[-1]
        model.addConstr(
            15 * t_dep[(m_dep, id_train_dep)] + Taches.T_DEP[m_dep] <= t_d[id_train_dep]
        )
        for m in Taches.TACHES_DEPART[:-1]:
            model.addConstr(
                15 * t_dep[(m, id_train_dep)] + Taches.T_DEP[m]
                <= 15 * t_dep[(m + 1, id_train_dep)]
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
        for id_arr_1 in tqdm(
            liste_id_train_arrivee,
            "Contrainte assurant qu'il n'y a qu'un train niveau de la machine DEB",
        ):
            for id_arr_2 in liste_id_train_arrivee:
                if id_arr_1 != id_arr_2:
                    delta_arr[(m_arr, id_arr_1, id_arr_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_arr_{m_arr}_{id_arr_1}_{id_arr_2}",
                    )

                    # Si delta = 1, alors id_arr_2 se termine avant id_arr_1
                    model.addConstr(
                        15 * t_arr[(m_arr, id_arr_2)] + Taches.T_ARR[m_arr]
                        <= 15 * t_arr[(m_arr, id_arr_1)]
                        + (1 - delta_arr[(m_arr, id_arr_1, id_arr_2)]) * M_big
                    )

                    # Si delta = 0, alors id_arr_1 se termine avant id_arr_2
                    model.addConstr(
                        15 * t_arr[(m_arr, id_arr_2)]
                        >= 15 * t_arr[(m_arr, id_arr_1)]
                        + Taches.T_ARR[m_arr]
                        - delta_arr[(m_arr, id_arr_1, id_arr_2)] * M_big
                    )

    delta_dep = {}

    for m_dep in tqdm(
        Taches.TACHES_DEP_MACHINE,
        "Contrainte assurant qu'il n'y a qu'un train niveau des machines FOR et DEG",
    ):
        for id_dep_1 in liste_id_train_depart:
            for id_dep_2 in liste_id_train_depart:
                if id_dep_1 != id_dep_2:
                    delta_dep[(m_dep, id_dep_1, id_dep_2)] = model.addVar(
                        vtype=grb.GRB.BINARY,
                        name=f"delta_dep_{m_dep}_{id_dep_1}_{id_dep_2}",
                    )

                    # Si delta = 1, alors id_dep_2 se termine avant id_dep_1
                    model.addConstr(
                        15 * t_dep[(m_dep, id_dep_2)] + Taches.T_DEP[m_dep]
                        <= 15 * t_dep[(m_dep, id_dep_1)]
                        + (1 - delta_dep[(m_dep, id_dep_1, id_dep_2)]) * M_big
                    )

                    # Si delta = 0, alors id_dep_1 se termine avant id_dep_2
                    model.addConstr(
                        15 * t_dep[(m_dep, id_dep_2)]
                        >= 15 * t_dep[(m_dep, id_dep_1)]
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
    Ajoute des contraintes pour respecter les horaires d'utilisation des machines.

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

    N_machines = {key: len(Limites_machines[key]) for key in Limites_machines.keys()}

    delta_lim_machine_DEB = {}

    if N_machines[Machines.DEB] > 0:
        for id_arr in tqdm(
            liste_id_train_arrivee, "Contrainte de fermeture de la machine DEB"
        ):
            delta_lim_machine_DEB[id_arr] = model.addVars(
                N_machines[Machines.DEB] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_DEB_{id_arr}",
            )  # N//2 + 1  contraintes
            # Premier cas : Avant la première limite
            model.addConstr(
                15 * t_arr[(3, id_arr)]
                <= Limites_machines[Machines.DEB][0]
                - Taches.T_ARR[3]
                + (1 - delta_lim_machine_DEB[id_arr][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEB] // 2):
                model.addConstr(
                    15 * t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][2 * i - 1]
                    - (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )
                model.addConstr(
                    15 * t_arr[(3, id_arr)]
                    <= Limites_machines[Machines.DEB][2 * i]
                    - Taches.T_ARR[3]
                    + (1 - delta_lim_machine_DEB[id_arr][i]) * M_big
                )

            # Dernier cas : Après la dernière limite (
            if N_machines[Machines.DEB] % 2 == 0:
                model.addConstr(
                    15 * t_arr[(3, id_arr)]
                    >= Limites_machines[Machines.DEB][-1]
                    - (1 - delta_lim_machine_DEB[id_arr][N_machines[Machines.DEB] // 2])
                    * M_big
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
        for id_dep in tqdm(
            liste_id_train_depart, "Contrainte de fermeture de la machine FOR"
        ):
            delta_lim_machine_FOR[id_dep] = model.addVars(
                N_machines[Machines.FOR] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_1_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                15 * t_dep[(1, id_dep)]
                <= Limites_machines[Machines.FOR][0]
                - Taches.T_DEP[1]
                + (1 - delta_lim_machine_FOR[id_dep][0]) * M_big
            )

            # Cas intermédiaires
            for i in range(1, N_machines[Machines.FOR] // 2):
                model.addConstr(
                    15 * t_dep[(1, id_dep)]
                    >= Limites_machines[Machines.FOR][2 * i - 1]
                    - (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    15 * t_dep[(1, id_dep)]
                    <= Limites_machines[Machines.FOR][2 * i]
                    - Taches.T_DEP[1]
                    + (1 - delta_lim_machine_FOR[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.FOR] % 2 == 0:
                model.addConstr(
                    15 * t_dep[(1, id_dep)]
                    >= Limites_machines[Machines.FOR][-1]
                    - (1 - delta_lim_machine_FOR[id_dep][N_machines[Machines.FOR] // 2])
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
        for id_dep in tqdm(
            liste_id_train_depart, "Contrainte de fermeture de la machine DEG"
        ):
            delta_lim_machine_DEG[id_dep] = model.addVars(
                N_machines[Machines.DEG] // 2 + 1,
                vtype=grb.GRB.BINARY,
                name=f"delta_machine_dep_3_{id_dep}",
            )

            # Premier cas : Avant la première limite
            model.addConstr(
                15 * t_dep[(3, id_dep)]
                <= Limites_machines[Machines.DEG][0]
                - Taches.T_DEP[3]
                + (1 - delta_lim_machine_DEG[id_dep][0]) * M_big
            )

            # Cas intermédiaires : Entre Limites
            for i in range(1, N_machines[Machines.DEG] // 2):
                model.addConstr(
                    15 * t_dep[(3, id_dep)]
                    >= Limites_machines[Machines.DEG][2 * i - 1]
                    - (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite inf
                model.addConstr(
                    15 * t_dep[(3, id_dep)]
                    <= Limites_machines[Machines.DEG][2 * i]
                    - Taches.T_DEP[3]
                    + (1 - delta_lim_machine_DEG[id_dep][i]) * M_big
                )  # Limite sup

            # Dernier cas : Après la dernière limite
            if N_machines[Machines.DEG] % 2 == 0:
                model.addConstr(
                    15 * t_dep[(3, id_dep)]
                    >= Limites_machines[Machines.DEG][-1]
                    - (1 - delta_lim_machine_DEG[id_dep][N_machines[Machines.DEG] // 2])
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

    N_chantiers = {key: len(Limites_chantiers[key]) for key in Limites_chantiers.keys()}

    delta_lim_chantier_rec = {1: {}, 2: {}, 3: {}}

    if N_chantiers[Chantiers.REC] > 0:
        for id_arr in tqdm(
            liste_id_train_arrivee, "Contrainte de fermeture du Chantier REC"
        ):
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
                    15 * t_arr[(m, id_arr)]
                    <= Limites_chantiers[Chantiers.REC][0]
                    - Taches.T_ARR[m]
                    + (1 - delta_lim_chantier_rec[m][id_arr][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.REC] // 2):
                    model.addConstr(
                        15 * t_arr[(m, id_arr)]
                        >= Limites_chantiers[Chantiers.REC][2 * i - 1]
                        - (1 - delta_lim_chantier_rec[m][id_arr][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15 * t_arr[(m, id_arr)]
                        <= Limites_chantiers[Chantiers.REC][2 * i]
                        - Taches.T_ARR[m]
                        + (1 - delta_lim_chantier_rec[m][id_arr][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.REC] % 2 == 0:
                    model.addConstr(
                        15 * t_arr[(m, id_arr)]
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
        for id_dep in tqdm(
            liste_id_train_depart, "Contrainte de fermeture du Chantier FOR"
        ):
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
                    15 * t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.FOR][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_for[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.FOR] // 2):
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.FOR][2 * i - 1]
                        - (1 - delta_lim_chantier_for[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.FOR][2 * i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_for[m][id_dep][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.FOR] % 2 == 0:
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
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
        for id_dep in tqdm(
            liste_id_train_depart, "Contrainte de fermeture du Chantier DEG"
        ):
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
                    15 * t_dep[(m, id_dep)]
                    <= Limites_chantiers[Chantiers.DEP][0]
                    - Taches.T_DEP[m]
                    + (1 - delta_lim_chantier_dep[m][id_dep][0]) * M_big
                )

                # Cas intermédiaires : Entre Limites
                for i in range(1, N_chantiers[Chantiers.DEP] // 2):
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
                        >= Limites_chantiers[Chantiers.DEP][2 * i - 1]
                        - (1 - delta_lim_chantier_dep[m][id_dep][i]) * M_big
                    )  # Limite inférieure (700)
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
                        <= Limites_chantiers[Chantiers.DEP][2 * i]
                        - Taches.T_DEP[m]
                        + (1 - delta_lim_chantier_dep[m][id_dep][i]) * M_big
                    )  # Limite supérieure (1500)

                # Dernier cas : Après la dernière limite (
                if N_chantiers[Chantiers.DEP] % 2 == 0:
                    model.addConstr(
                        15 * t_dep[(m, id_dep)]
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
    for id_dep in tqdm(
        liste_id_train_depart,
        "Contrainte assurant la succession des tâches entre les chantiers de REC et FOR",
    ):
        for id_arr in dict_correspondances[id_dep]:
            model.addConstr(
                15 * t_dep[(1, id_dep)] >= 15 * t_arr[(3, id_arr)] + Taches.T_ARR[3]
            )
    return True


def contraintes_nombre_voies(
    model: grb.Model,
    t_arr: dict,
    t_dep: dict,
    t_a: dict,
    t_d: dict,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    limites_voies: dict,
    is_present: dict,
    premier_wagon: dict,
    temps_max: int,
    temps_min: int = 0,
) -> bool:
    """
    Ajoute des contraintes limitant le nombre de
    trains présents sur un même chantier à tout instant.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour ajouter les contraintes.
    t_arr : dict
        Temps de début des tâches d'arrivée.
    t_dep : dict
        Temps de début des tâches de départ'.
    t_a : dict
        Temps d'arrivée des trains en gare.
    t_d : dict
        Temps de départ des trains.
    liste_id_train_arrivee : list
        Identifiants des trains d'arrivée'.
    liste_id_train_depart : list
        Identifiants des trains de départ.
    limites_voies : dict
        Nombre de voies utilisables par chantier.
    is_present : dict
        Présence ou non du train id_train sur un chantier.
    temps_min : int
        Heure d'arrivée du premier train (permet de réduire le nombre de variables à créer)
    temps_max : int
        Heure de départ du dernier train (permet de réduire le nombre de variables à créer)
    premier_wagon : dict
        Variables de temps du début de la première tâche de débranchement
        sur les trains d'arrivée contenant des wagons du train de départ

    Retourne :
    ----------
    bool
        True si les contraintes sont ajoutées.
    """

    Mbig = 1000000
    eps = 0.1

    # Créer des variables binaires : est-ce que le train est présent ?
    before_upper_bound = {
        Chantiers.REC: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"before_ub_REC_{id_train}_{t}"
            )
            for id_train in liste_id_train_arrivee
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.FOR: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"before_ub_FOR_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.DEP: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"before_ub_DEP_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
    }

    after_lower_bound = {
        Chantiers.REC: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"after_lb_REC_{id_train}_{t}"
            )
            for id_train in liste_id_train_arrivee
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.FOR: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"after_lb_FOR_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.DEP: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"after_lb_DEP_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
    }

    for id_train in liste_id_train_arrivee:
        for t in range(temps_min, temps_max + 1):  # Parcours du temps
            # Si le train est présent, t_start <= t <= t_end
            # is_present => t_arr[(1, id_train)] <= t
            model.addConstr(
                15 * t
                >= t_a[id_train]
                - Mbig * (1 - after_lower_bound[Chantiers.REC][(id_train, t)]),
                name=f"after_lower_bound_REC_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                <= t_a[id_train]
                - eps
                + Mbig * after_lower_bound[Chantiers.REC][(id_train, t)],
                name="bigM_constr_REC_after_lb",
            )

            model.addConstr(
                15 * t
                <= 15 * t_arr[(3, id_train)]
                + Taches.T_ARR[3]
                + Mbig * (1 - before_upper_bound[Chantiers.REC][(id_train, t)]),
                name=f"before_upper_bound_REC_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                >= 15 * t_arr[(3, id_train)]
                + Taches.T_ARR[3]
                + eps
                - Mbig * before_upper_bound[Chantiers.REC][(id_train, t)],
                name="bigM_constr_REC_before_ub",
            )

            model.addGenConstrAnd(
                is_present[Chantiers.REC][(id_train, t)],
                [
                    after_lower_bound[Chantiers.REC][(id_train, t)],
                    before_upper_bound[Chantiers.REC][(id_train, t)],
                ],
                "andconstr_REC",
            )

    for id_train in liste_id_train_depart:
        for t in range(temps_min, temps_max + 1):  # Parcours du temps
            # Si le train est présent, t_start <= t <= t_end
            model.addConstr(
                15 * t
                >= 15 * premier_wagon[id_train]
                - Mbig * (1 - after_lower_bound[Chantiers.FOR][(id_train, t)]),
                name=f"after_lower_bound_FOR_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                <= 15 * premier_wagon[id_train]
                - eps
                + Mbig * after_lower_bound[Chantiers.FOR][(id_train, t)],
                name="bigM_constr_FOR_after_lb",
            )

            model.addConstr(
                15 * t
                <= 15 * t_dep[(3, id_train)]
                + Taches.T_DEP[3]
                + Mbig * (1 - before_upper_bound[Chantiers.FOR][(id_train, t)]),
                name=f"before_upper_bound_FOR_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                >= 15 * t_dep[(3, id_train)]
                + Taches.T_DEP[3]
                + eps
                - Mbig * before_upper_bound[Chantiers.FOR][(id_train, t)],
                name="bigM_constr_FOR_before_ub",
            )

            model.addGenConstrAnd(
                is_present[Chantiers.FOR][(id_train, t)],
                [
                    after_lower_bound[Chantiers.FOR][(id_train, t)],
                    before_upper_bound[Chantiers.FOR][(id_train, t)],
                ],
                "andconstr_FOR",
            )

            model.addConstr(
                15 * t
                >= 15 * t_dep[(3, id_train)]
                - Mbig * (1 - after_lower_bound[Chantiers.DEP][(id_train, t)]),
                name=f"after_lower_bound_DEP_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                <= 15 * t_dep[(3, id_train)]
                + eps
                + Mbig * after_lower_bound[Chantiers.DEP][(id_train, t)],
                name="bigM_constr_DEP_after_lb",
            )

            model.addConstr(
                15 * t
                <= t_d[id_train]
                + Mbig * (1 - before_upper_bound[Chantiers.DEP][(id_train, t)]),
                name=f"before_upper_bound_DEP_{id_train}_{t}",
            )
            model.addConstr(
                15 * t
                >= t_d[id_train]
                + eps
                - Mbig * before_upper_bound[Chantiers.DEP][(id_train, t)],
                name="bigM_constr_DEP_before_ub",
            )

            model.addGenConstrAnd(
                is_present[Chantiers.DEP][(id_train, t)],
                [
                    after_lower_bound[Chantiers.DEP][(id_train, t)],
                    before_upper_bound[Chantiers.DEP][(id_train, t)],
                ],
                "andconstr_DEP",
            )

    for t in tqdm(
        range(temps_min, temps_max + 1),
        "Contrainte relative au nombre de voies des chantiers",
    ):
        model.addConstr(
            grb.quicksum(
                [
                    is_present[Chantiers.REC][(id_train, t)]
                    for id_train in liste_id_train_arrivee
                ]
            )
            <= limites_voies[Chantiers.REC]
        )

        model.addConstr(
            grb.quicksum(
                [
                    is_present[Chantiers.FOR][(id_train, t)]
                    for id_train in liste_id_train_depart
                ]
            )
            <= limites_voies[Chantiers.FOR]
        )
        model.addConstr(
            grb.quicksum(
                [
                    is_present[Chantiers.DEP][(id_train, t)]
                    for id_train in liste_id_train_depart
                ]
            )
            <= limites_voies[Chantiers.DEP]
        )

    return True


def contraintes_premier_wagon(
    model: grb.Model,
    t_arr: dict,
    dict_correspondances: list,
    liste_id_train_depart: list,
    premier_wagon: dict,
) -> bool:
    """
    Ajoute les contraintes définissant le temps du
    premier débranchement de wagon du train de départ.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour ajouter les contraintes.
    t_arr : dict
        Temps de début des tâches d'arrivée.
    dict_correspondances : dict
        Correspondances entre trains d'arrivée et de départ.
    liste_id_train_depart : list
        Identifiants des trains de départ.
    premier_wagon : dict
        Variables de temps du début de la première tâche de débranchement
        sur les trains d'arrivée contenant des wagons du train de départ.

    Retourne :
    ----------
    bool
        True si les contraintes sont ajoutées.
    """

    for id_train_depart in tqdm(
        liste_id_train_depart,
        "Contrainte définissant le temps de débranchement du premier wagon d'un train de départ",
    ):
        model.addConstr(
            premier_wagon[id_train_depart]
            == grb.min_(
                [
                    t_arr[3, id_train_arrivee]
                    for id_train_arrivee in dict_correspondances[id_train_depart]
                ]
            )
        )

    return True


def contrainte_nombre_max_agents(
    model: grb.Model,
    nombre_roulements: int,
    nombre_cycles_agents: dict,
    nombre_agents: dict,
    max_agents_sur_roulement: dict,
    nb_cycle_jour,
) -> bool:
    for r in range(1, nombre_roulements + 1):
        for q in range(nombre_cycles_agents[r] // nb_cycle_jour[r]):
            model.addConstr(
                grb.quicksum(
                    [
                        nombre_agents[(r, nb_cycle_jour[r] * q + i)]
                        for i in range(1, nb_cycle_jour[r] + 1)
                    ]
                )
                <= max_agents_sur_roulement[r]
            )

    return True


def unicite_roulement_et_cycle(
    model,
    equip,
    nb_cycles_agents,
    liste_id_train_arrivee,
    liste_id_train_depart,
    who_arr,
    who_dep,
    h_deb,
):
    r_sur_m_arr = {m: equip[("arr", m)] for m in [1, 2, 3]}
    r_sur_m_dep = {m: equip[("dep", m)] for m in [1, 2, 3, 4]}

    for m in [1, 2, 3]:
        for id_train in liste_id_train_arrivee:
            model.addConstr(
                grb.quicksum(
                    [
                        who_arr[(m, id_train, r, k, t)]
                        for r in r_sur_m_arr[m]
                        for k in range(1, nb_cycles_agents[r] + 1)
                        for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12)
                    ]
                )
                >= Taches.T_ARR[m] // 5
            )

    for m in [1, 2, 3, 4]:
        for id_train in liste_id_train_depart:
            model.addConstr(
                grb.quicksum(
                    [
                        who_dep[(m, id_train, r, k, t)]
                        for r in r_sur_m_dep[m]
                        for k in range(1, nb_cycles_agents[r] + 1)
                        for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12)
                    ]
                )
                >= Taches.T_DEP[m] // 5
            )


def non_saturation_personnel(
    model,
    nombre_roulements,
    nb_cycles,
    h_deb,
    who_arr,
    who_dep,
    liste_id_train_arrivee,
    liste_id_train_depart,
    comp_arr,
    comp_dep,
    nombre_agents,
):
    for r in range(1, nombre_roulements + 1):
        for k in range(1, nb_cycles[r] + 1):
            for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12):
                model.addConstr(
                    grb.quicksum(
                        [
                            who_arr[(m, id_train, r, k, t)]
                            for id_train in liste_id_train_arrivee
                            for m in comp_arr[r]
                        ]
                    )
                    + grb.quicksum(
                        [
                            who_dep[(m, id_train, r, k, t)]
                            for id_train in liste_id_train_depart
                            for m in comp_dep[r]
                        ]
                    )
                    <= nombre_agents[(r, k)]
                )


def contrainte_cohérence_who_t(
    model,
    equip,
    liste_id_train_arrivee,
    liste_id_train_depart,
    nb_cycles,
    who_arr,
    who_dep,
    h_deb,
    t_arr,
    t_dep,
):
    eps = 0.1
    M_big = 100000000
    r_sur_m_arr = {m: equip[("arr", m)] for m in [1, 2, 3]}
    r_sur_m_dep = {m: equip[("dep", m)] for m in [1, 2, 3, 4]}
    for m in [1, 2, 3]:
        for id_train in liste_id_train_arrivee:
            for r in r_sur_m_arr[m]:
                for k in range(1, nb_cycles[r] + 1):
                    for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12):
                        model.addConstr(
                            15 * t_arr[(m, id_train)]
                            <= 5 * t + M_big * (1 - who_arr[(m, id_train, r, k, t)])
                        )
                        model.addConstr(
                            5 * t
                            <= 15 * t_arr[(m, id_train)]
                            + Taches.T_ARR[m]
                            + eps
                            + M_big * (1 - who_arr[(m, id_train, r, k, t)])
                        )
    for m in [1, 2, 3, 4]:
        for id_train in liste_id_train_depart:
            for r in r_sur_m_dep[m]:
                for k in range(1, nb_cycles[r] + 1):
                    for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12):
                        model.addConstr(
                            15 * t_dep[(m, id_train)]
                            <= 5 * t + M_big * (1 - who_dep[(m, id_train, r, k, t)])
                        )
                        model.addConstr(
                            5 * t
                            <= 15 * t_dep[(m, id_train)]
                            + Taches.T_DEP[m]
                            + eps
                            + M_big * (1 - who_dep[(m, id_train, r, k, t)])
                        )


def contrainte_unicite_who_cycle(
    model,
    equip,
    liste_id_train_arrivee,
    liste_id_train_depart,
    nb_cycles,
    who_arr,
    who_dep,
    h_deb,
    t_arr,
    t_dep,
):
    M_big = 100000000
    r_sur_m_arr = {m: equip[("arr", m)] for m in [1, 2, 3]}
    r_sur_m_dep = {m: equip[("dep", m)] for m in [1, 2, 3, 4]}
    for m in [1, 2, 3]:
        for id_train in liste_id_train_arrivee:
            for r in r_sur_m_arr[m]:
                for k in range(1, nb_cycles[r] + 1):
                    for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12):
                        model.addConstr(
                            h_deb[(r, k)]
                            <= 15 * t_arr[(m, id_train)]
                            + M_big * (1 - who_arr[(m, id_train, r, k, t)])
                        )
                        model.addConstr(
                            15 * t_arr[(m, id_train)] + Taches.T_ARR[m]
                            <= h_deb[(r, k)]
                            + 8 * 60
                            + M_big * (1 - who_arr[(m, id_train, r, k, t)])
                        )
    for m in [1, 2, 3, 4]:
        for id_train in liste_id_train_depart:
            for r in r_sur_m_dep[m]:
                for k in range(1, nb_cycles[r] + 1):
                    for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12):
                        model.addConstr(
                            h_deb[(r, k)]
                            <= 15 * t_dep[(m, id_train)]
                            + M_big * (1 - who_dep[(m, id_train, r, k, t)])
                        )
                        model.addConstr(
                            15 * t_dep[(m, id_train)] + Taches.T_DEP[m]
                            <= h_deb[(r, k)]
                            + 8 * 60
                            + M_big * (1 - who_dep[(m, id_train, r, k, t)])
                        )
