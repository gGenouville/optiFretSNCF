"""
Module de gestion des opérations sur les trains utilisant Gurobi pour l'optimisation.

Ce module définit les tâches et contraintes pour la planification des opérations
sur les trains, incluant les tâches d'arrivée et de départ, ainsi que les
contraintes temporelles et de succession.

Fonctions :
-----------
init_model : Initialise le modèle Gurobi avec les contraintes de base.
init_model2 : Initialise le modèle Gurobi avec les contraintes sur l'attribution des tâches aux agents.
init_variables : Initialise les variables de décision de base.
init_variables2 : Initialise les variables de décision sur l'attribution des tâches aux agents.
variables_debut_tache_arrive : Initialise les variables
    de début des tâches pour les trains d'arrivée.
variables_debut_tache_depart : Initialise les variables
    de début des tâches pour les trains de départ.
variable_is_present : Initialise les variables de
    présence des trains sur les différents chantiers.
variable_premier_wagon : Initialise les variables de temps du début de la première tâche
    de débranchement sur les trains d'arrivée contenant des wagons du train de départ.
variable_agents : Initialise les variables représentant le nombre d'agents utilisés
    sur le cycle k du roulement r.
variable_who : Initialise les variables binaires who_arr et who_dep représentant 
    l'utilisation ou non d'un agent d'un roulement r d'un cycle k pour une tache 
    réalisée m sur un train n à un instant t donné. 
variable_decomp : Initialise les variables décomposant les variables de début des tâches pour les
    trains à l'arrivée et au départ en leur numéro de cycle et leur temps dans le cycle.
init_objectif : Crée la variable à minimiser de la fonction object ainsi que ses contraintes 
    (minimisation du nombre maximal de voies sur le chantier de Formation).
init_objectif2 : Crée la variable à minimiser de la fonction object ainsi que ses contraintes 
    (minimisation du nomnbre de journées de service).
"""

import gurobipy as grb

from module.contraintes import init_contraintes, init_contraintes2
from module.constants import Chantiers, Taches


def init_model(
    liste_id_train_arrivee: list,
    t_a: dict,
    liste_id_train_depart: list,
    t_d: dict,
    dict_correspondances: dict,
    limites_voies: dict,
    temps_max: int,
    temps_min: int,
    limites_chantiers: dict,
    limites_machines: dict,
    nb_cycle_agents: dict,
) -> tuple[grb.Model, dict, dict, dict]:
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
    id_file : int
        Identifiant du fichier.
    limites_voies : dict
        Nombre de voies utilisables par chantier.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ---------
    grb.Model
        Modèle d'optimisation Gurobi initialisé.
    tuple
        Variables du modèle (t_arr, t_dep).
    """
    model = grb.Model("SNCF JALON 3.1")

    t_arr, t_dep, is_present, premier_wagon, hat_arr, hat_dep, k_arr, k_dep = (
        init_variables(
            model,
            liste_id_train_arrivee,
            liste_id_train_depart,
            temps_min,
            temps_max,
        )
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
        limites_voies,
        is_present,
        premier_wagon,
        temps_max,
        temps_min,
        limites_chantiers,
        limites_machines,
        hat_arr,
        hat_dep,
        k_arr,
        k_dep,
    )

    init_objectif(
        model,
        liste_id_train_arrivee,
        liste_id_train_depart,
        k_arr,
        k_dep,
        nb_cycle_agents,
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model, t_arr, t_dep, is_present


def init_model2(
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    nb_cycles_agents,
    h_deb,
    nombre_roulements,
    equip,
    max_agents_sur_roulement,
    comp_arr,
    comp_dep,
    nb_cycle_jour,
    t_arr,
    t_dep,
) -> tuple[grb.Model, dict, dict, dict]:
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
    id_file : int
        Identifiant du fichier.
    limites_voies : dict
        Nombre de voies utilisables par chantier.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ---------
    grb.Model
        Modèle d'optimisation Gurobi initialisé.
    tuple
        Variables du modèle (t_arr, t_dep).
    """
    model2 = grb.Model("SNCF JALON 3.2")

    who_arr, who_dep, nombre_agents = init_variables2(
        model2,
        liste_id_train_arrivee,
        liste_id_train_depart,
        nb_cycles_agents,
        h_deb,
        nombre_roulements,
        max_agents_sur_roulement,
        equip,
    )

    init_contraintes2(
        model2,
        t_arr,
        liste_id_train_arrivee,
        t_dep,
        liste_id_train_depart,
        nombre_roulements,
        nb_cycles_agents,
        nombre_agents,
        max_agents_sur_roulement,
        equip,
        h_deb,
        who_arr,
        who_dep,
        comp_arr,
        comp_dep,
        nb_cycle_jour,
    )

    init_objectif2(model2, nombre_agents, nombre_roulements, nb_cycles_agents)

    # Choix d'un paramétrage d'affichage
    model2.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model2.update()

    return model2, who_arr, who_dep, nombre_agents


def init_variables(
    m: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    temps_min: int,
    temps_max: int,
) -> tuple[dict, dict, dict, dict]:
    """
    Initialise les variables de début des tâches pour les trains,
    de présence sur un chantier de premier débranchement de wagon.

    Paramètres :
    -----------
    m : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ---------
    tuple[dict, dict, dict, dict]
        - Variables des débuts de tâches d'arrivée.
        - Variables des débuts de tâches de départ.
        - Variables de présence dans les voies.
        - Variables de début de la première tâche de
            débranchement sur les wagons du train de départ.
    """
    t_arr = variables_debut_tache_arrive(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)
    is_present = variable_is_present(
        m, liste_id_train_arrivee, liste_id_train_depart, temps_min, temps_max
    )
    premier_wagon = variable_premier_wagon(m, liste_id_train_depart)
    hat_arr, hat_dep, k_arr, k_dep = variable_decomp(
        m, liste_id_train_arrivee, liste_id_train_depart
    )

    return t_arr, t_dep, is_present, premier_wagon, hat_arr, hat_dep, k_arr, k_dep


def init_variables2(
    m: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    nb_cycles_agents,
    h_deb,
    nombre_roulements,
    roulements_agents,
    equip,
) -> tuple[dict, dict, dict, dict]:
    """
    Initialise les variables de début des tâches pour les trains,
    de présence sur un chantier de premier débranchement de wagon.

    Paramètres :
    -----------
    m : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ---------
    tuple[dict, dict, dict, dict]
        - Variables des débuts de tâches d'arrivée.
        - Variables des débuts de tâches de départ.
        - Variables de présence dans les voies.
        - Variables de début de la première tâche de
            débranchement sur les wagons du train de départ.
    """
    who_arr, who_dep = variable_who(
        m,
        nb_cycles_agents,
        liste_id_train_arrivee,
        liste_id_train_depart,
        equip,
        h_deb,
    )
    nb_agents = variable_agents(
        m, nombre_roulements, nb_cycles_agents, roulements_agents
    )

    return who_arr, who_dep, nb_agents


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


def variable_is_present(
    model: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    temps_min: int,
    temps_max: int,
) -> dict:
    """
    Initialise les variables de présence des trains sur les différents chantiers.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ---------
    dict
        Variables de présence des trains sur les chantiers
        à un instant t, indexées par (chantier, train, temps).
    """
    is_present = {
        Chantiers.REC: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"is_present_REC_{id_train}_{t}"
            )
            for id_train in liste_id_train_arrivee
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.FOR: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"is_present_FOR_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
        Chantiers.DEP: {
            (id_train, t): model.addVar(
                vtype=grb.GRB.BINARY, name=f"is_present_DEP_{id_train}_{t}"
            )
            for id_train in liste_id_train_depart
            for t in range(temps_min, temps_max + 1)
        },
    }
    return is_present


def variable_premier_wagon(
    model: grb.Model,
    liste_id_train_depart: list,
) -> dict:
    """
    Initialise les variables de temps du début de la première tâche de
    débranchement sur les trains d'arrivée contenant des wagons du train de départ.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    dict
        Variables de temps du début de la première tâche de débranchement sur les trains
        d'arrivée contenant des wagons du train de départ, indexées par identifiant de train de départ.
    """
    premier_wagon = {
        id_train: model.addVar(vtype=grb.GRB.INTEGER,
                               name=f"premier_wagon_{id_train}")
        for id_train in liste_id_train_depart
    }
    return premier_wagon


def variable_agents(
    model, nombre_roulements, nb_cycles_agents, max_agents_sur_roulement
):
    nombre_agents = {
        (r, k): model.addVar(
            vtype=grb.GRB.INTEGER,
            lb=0,
            ub=max_agents_sur_roulement[r],
            name=f"Nombre_agents_roulement_{r}_cycle_{k}",
        )
        for r in range(1, nombre_roulements + 1)
        for k in range(1, nb_cycles_agents[r] + 1)
    }
    return nombre_agents


def variable_who(
    model: grb.Model,
    nb_cycles_agents: dict,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    equip: dict,
    h_deb: dict,
):
    """
    Définit des variables binaires indiquant si un agent effectue une tâche 
    d'arrivée ou de départ à un instant donné dans un modèle d'optimisation.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    nb_cycles_agents : dict
        Nombre de cycles pour chaque agent.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.
    equip : dict
        Agents autorisés pour chaque tâche.
    h_deb : dict
        Heures de début des cycles des agents.

    Retourne :
    ---------
    tuple[dict, dict]
        - Variables binaires pour les tâches d'arrivée indexées par tâche, train, agent, cycle et temps.
        - Variables binaires pour les tâches de départ indexées par tâche, train, agent, cycle et temps.
    """

    who_arr = {
        (m, n, r, k, t): model.addVar(
            vtype=grb.GRB.BINARY,
            name=f"Bool_roulement_{r}_réalise_tâche_arr_{m}_au_cycle_{k}_au_temps_{t}",
        )
        for m in Taches.TACHES_ARRIVEE
        for n in liste_id_train_arrivee
        for r in equip[("arr", m)]
        for k in range(1, nb_cycles_agents[r] + 1)
        for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12)
    }
    who_dep = {
        (m, n, r, k, t): model.addVar(
            vtype=grb.GRB.BINARY,
            name=f"Bool_roulement_{r}_réalise_tâche_dep_{m}_au_cycle_{k}_au_temps_{t}",
        )
        for m in Taches.TACHES_DEPART
        for n in liste_id_train_depart
        for r in equip[("dep", m)]
        for k in range(1, nb_cycles_agents[r] + 1)
        for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12)
    }
    return who_arr, who_dep


def variable_decomp(
    model: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
) -> dict:
    """
    Initialise les variables décomposant les variables de début des tâches pour les
    trains à l'arrivée et au départ en leur numéro de cycle et leur temps dans le cycle.

    Paramètres :
    -----------
    model : grb.Model
        Modèle d'optimisation Gurobi.
    liste_id_train_arrivee : list
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : list
        Identifiants des trains au départ.

    Retourne :
    ---------
    tuple[dict, dict, dict, dict]
        - Variables de temps dans le cycle des débuts de tâches d'arrivée.
        - Variables de temps dans le cycle des débuts de tâches de départ.
        - Variables de numéro de cycle des débuts de tâches d'arrivée.
        - Variables de numéro de cycle des débuts de tâches de départ.
    """
    hat_arr = {
        (m, id_train_arr): model.addVar(
            vtype=grb.GRB.INTEGER, lb=0, ub=8 * 4 - 1, name="t"
        )
        for m in Taches.TACHES_ARRIVEE
        for id_train_arr in liste_id_train_arrivee
    }
    hat_dep = {
        (m, id_train_arr): model.addVar(
            vtype=grb.GRB.INTEGER, lb=0, ub=8 * 4 - 1, name="t"
        )
        for m in Taches.TACHES_DEPART
        for id_train_arr in liste_id_train_depart
    }
    k_arr = {
        (m, id_train_arr): model.addVar(vtype=grb.GRB.INTEGER, lb=0, name="t")
        for m in Taches.TACHES_ARRIVEE
        for id_train_arr in liste_id_train_arrivee
    }
    k_dep = {
        (m, id_train_arr): model.addVar(vtype=grb.GRB.INTEGER, lb=0, name="t")
        for m in Taches.TACHES_DEPART
        for id_train_arr in liste_id_train_depart
    }
    return hat_arr, hat_dep, k_arr, k_dep


def init_objectif(
    model: grb.Model,
    liste_id_train_arrivee: dict,
    liste_id_train_depart: dict,
    k_arr: dict,
    k_dep: dict,
    nb_cycle_agents: dict,
) -> bool:
    """
    Crée la fonction objectif à minimiser ainsi que les contraintes associées.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour l'optimisation.
    liste_id_train_arrivee : dict
        Identifiants des trains à l'arrivée.
    liste_id_train_depart : dict
        Identifiants des trains au départ.
    k_arr : dict
        Cycles d'affectation des tâches d'arrivée par train.
    k_dep : dict
        Cycles d'affectation des tâches de départ par train.
    nb_cycle_agents : dict
        Nombre de cycles pour chaque agent.

    Retourne :
    ----------
    bool
        True si la fonction objectif est bien ajoutée au modèle.
    """
    K = nb_cycle_agents[1]
    M_big = K
    eps = 0.1

    delta_arr = {
        (k, m, n, x): model.addVar(vtype=grb.GRB.BINARY, name="delta_arr_{k}_{m}_{n}")
        for n in liste_id_train_arrivee
        for m in Taches.TACHES_ARRIVEE
        for k in range(K)
        for x in [-1, 0, 1]
    }
    delta_dep = {
        (k, m, n, x): model.addVar(vtype=grb.GRB.BINARY, name="delta_dep_{k}_{m}_{n}")
        for n in liste_id_train_depart
        for m in Taches.TACHES_DEPART
        for k in range(K)
        for x in [-1, 0, 1]
    }

    max_t = model.addVar(vtype=grb.GRB.INTEGER, lb=0, name="max_t")

    for k in range(K):
        for n in liste_id_train_arrivee:
            for m in Taches.TACHES_ARRIVEE:
                model.addConstr(k_arr[m, n] - k + eps <=
                                M_big * delta_arr[k, m, n, 1])
                model.addConstr(
                    k - k_arr[m, n] - eps <= M_big *
                    (1 - delta_arr[k, m, n, 1])
                )
                model.addConstr(k - k_arr[m, n] + eps <=
                                M_big * delta_arr[k, m, n, -1])
                model.addConstr(
                    k_arr[m, n] - k - eps <= M_big *
                    (1 - delta_arr[k, m, n, -1])
                )
                model.addConstr(
                    delta_arr[k, m, n, 0] >= delta_arr[k,
                                                       m, n, 1]+delta_arr[k, m, n, -1]-1
                )
        for n in liste_id_train_depart:
            for m in Taches.TACHES_DEPART:
                model.addConstr(k_dep[m, n] - k + eps <=
                                M_big * delta_dep[k, m, n, 1])
                model.addConstr(
                    k - k_dep[m, n] - eps <= M_big *
                    (1 - delta_dep[k, m, n, 1])
                )
                model.addConstr(k - k_dep[m, n] + eps <=
                                M_big * delta_dep[k, m, n, -1])
                model.addConstr(
                    k_dep[m, n] - k - eps <= M_big *
                    (1 - delta_dep[k, m, n, -1])
                )
                model.addConstr(
                    delta_dep[k, m, n, 0] >= delta_dep[k,
                                                       m, n, 1]+delta_dep[k, m, n, -1]-1
                )
        model.addConstr(
            max_t
            >= grb.quicksum(
                [
                    delta_arr[k, m, n, 0]
                    for n in liste_id_train_arrivee
                    for m in Taches.TACHES_ARRIVEE
                ]
            )
            + grb.quicksum(
                [
                    delta_dep[k, m, n, 0]
                    for n in liste_id_train_depart
                    for m in Taches.TACHES_DEPART
                ]
            )
        )

    model.setObjective(
        max_t,
        grb.GRB.MINIMIZE,
    )

    return True


def init_objectif2(
    model: grb.Model,
    nombre_agents: dict,
    nombre_roulements: int,
    nb_cycles_agents: dict,
) -> bool:
    """
    Crée la fonction objectif à minimiser ainsi que les contraintes associées.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour l'optimisation.
    nombre_agents : dict
        Variables représentant le nombre d'agents affectés par roulement et cycle.
    nombre_roulements : int
        Nombre total de roulements disponibles.
    nb_cycles_agents : dict
        Nombre de cycles pour chaque agent.

    Retourne :
    ----------
    bool
        True si la fonction objectif est bien ajoutée au modèle.
    """

    model.setObjective(
        grb.quicksum(
            [
                nombre_agents[(r, k)]
                for r in range(1, nombre_roulements + 1)
                for k in range(1, nb_cycles_agents[r] + 1)
            ]
        ),
        grb.GRB.MINIMIZE,
    )

    return True
