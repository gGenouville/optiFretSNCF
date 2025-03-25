"""
Module de gestion des opérations sur les trains utilisant Gurobi pour l'optimisation.

Ce module définit les tâches et contraintes pour la planification des opérations
sur les trains, incluant les tâches d'arrivée et de départ, ainsi que les
contraintes temporelles et de succession.

Fonctions :
-----------
init_model : Initialise le modèle Gurobi avec les contraintes de base.
init_variables: Initialise les variables de décision.
variables_debut_tache_arrive : Initialise les variables
    de début des tâches pour les trains d'arrivée.
variables_debut_tache_depart : Initialise les variables
    de début des tâches pour les trains de départ.
variable_is_present : Initialise les variables de
    présence des trains sur les différents chantiers.
variable_premier_wagon : Initialise les variables de temps du début de la première tâche
    de débranchement sur les trains d'arrivée contenant des wagons du train de départ.
init_objectif : Crée la variable à minimiser de la fonction object ainsi que ses contraintes.
"""

import gurobipy as grb

from module.contraintes2 import init_contraintes
from module.utils2 import Chantiers, Taches


def init_model(
    liste_id_train_arrivee: list,
    t_a: dict,
    liste_id_train_depart: list,
    t_d: dict,
    dict_correspondances: dict,
    file: str,
    id_file: int,
    limites_voies: dict,
    temps_max: int,
    temps_min: int,
    nb_cycles_agents,
    heure_debut_roulement,
    nombre_roulements,
    equip,
    max_agents_sur_roulement,
    h_deb,
    comp_arr,
    comp_dep,
    nb_cycle_jour
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
    model = grb.Model("SNCF JALON 1")

    t_arr, t_dep, is_present, premier_wagon, who_arr, who_dep, nombre_agents = init_variables(
        model,
        liste_id_train_arrivee,
        liste_id_train_depart,
        temps_min,
        temps_max,
        file,
        nb_cycles_agents,
        heure_debut_roulement,
        nombre_roulements,
        max_agents_sur_roulement,
        equip,
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
        is_present,
        premier_wagon,
        temps_max,
        temps_min,
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
        nb_cycle_jour
    )

    init_objectif(
        model,
        nombre_agents,
        nombre_roulements,
        nb_cycles_agents
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model, t_arr, t_dep, is_present, who_arr, who_dep


def init_variables(
    m: grb.Model,
    liste_id_train_arrivee: list,
    liste_id_train_depart: list,
    temps_min: int,
    temps_max: int,
    file,
    nb_cycles_agents,
    heure_debut_roulement,
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
    t_arr = variables_debut_tache_arrive(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)
    is_present = variable_is_present(
        m, liste_id_train_arrivee, liste_id_train_depart, temps_min, temps_max
    )
    premier_wagon = variable_premier_wagon(m, liste_id_train_depart)
    who_arr, who_dep = variable_who(
        m,
        nb_cycles_agents,
        liste_id_train_arrivee,
        liste_id_train_depart,
        equip,
        heure_debut_roulement,
    )
    nb_agents = variable_agents(
        m, nombre_roulements, nb_cycles_agents, roulements_agents
    )

    return t_arr, t_dep, is_present, premier_wagon, who_arr, who_dep, nb_agents


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
        id_train: model.addVar(vtype=grb.GRB.INTEGER, name=f"premier_wagon_{id_train}")
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
    model,
    nb_cycles_agents,
    liste_id_train_arrivee,
    liste_id_train_depart,
    equip,
    h_deb,
):
    who_arr = {
        (m, n, r, k, t): model.addVar(
            vtype=grb.GRB.BINARY,
            name=f"Bool_roulement_{r}_réalise_tâche_arr_{m}_au_cycle_{k}_au_temps_{t}",
        )
        for m in [1, 2, 3]
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
        for m in [1, 2, 3, 4]
        for n in liste_id_train_depart
        for r in equip[("dep", m)]
        for k in range(1, nb_cycles_agents[r] + 1)
        for t in range(h_deb[(r, k)] // 5, h_deb[(r, k)] // 5 + 8 * 12)
    }
    return who_arr, who_dep


def init_objectif(
    model: grb.Model,
    nombre_agents: dict,
    nombre_roulements: int,
    nb_cycles_agents: dict,
) -> bool:
    """
    Crée la variable à minimiser de la fonction object ainsi que ses contraintes.

    Paramètres :
    ------------
    model : grb.Model
        Modèle Gurobi pour ajouter les contraintes.
    is_present : dict
        Présence ou non du train id_train sur un chantier.
    liste_id_train_depart : list
        Identifiants des trains de départ.
    temps_min : int
        Temps d'arrivée du premier train.
    temps_max : int
        Temps de départ du dernier train.

    Retourne :
    ----------
    bool
        True si la fonction objectif est ajoutée.
    """
    
    model.setObjective(grb.quicksum([nombre_agents[(r,k)] for r in range(1, nombre_roulements + 1)
        for k in range(1, nb_cycles_agents[r] + 1)]), grb.GRB.MINIMIZE)

    return True
