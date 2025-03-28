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
        Variables du modèle (t_arr, t_dep, is_present).
    """
    model = grb.Model("SNCF JALON 3")

    t_arr, t_dep, is_present, premier_wagon, t_arr15, t_dep15 = init_variables(
        model,
        liste_id_train_arrivee,
        liste_id_train_depart,
        temps_min,
        temps_max,
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
        t_arr15,
        t_dep15
    )

    init_objectif(
        model,
        is_present,
        liste_id_train_depart,
        temps_min,
        temps_max,
    )

    # Choix d'un paramétrage d'affichage
    model.params.outputflag = 0  # mode muet
    # Mise à jour du modèle
    model.update()

    return model, t_arr, t_dep, is_present


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
    t_arr15 = variables_debut_tache_arrive_machine(m, liste_id_train_arrivee)
    t_dep = variables_debut_tache_depart(m, liste_id_train_depart)
    t_dep15 = variables_debut_tache_depart_machine(m, liste_id_train_depart)
    is_present = variable_is_present(
        m, liste_id_train_arrivee, liste_id_train_depart, temps_min, temps_max
    )
    premier_wagon = variable_premier_wagon(m, liste_id_train_depart)

    return t_arr, t_dep, is_present, premier_wagon, t_arr15, t_dep15


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

def variables_debut_tache_arrive_machine(
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
    t_arr15 = {
        (m, id_train_arr): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_ARR_MACHINE
        for id_train_arr in liste_id_train_arrivee
    }
    return t_arr15


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

def variables_debut_tache_depart_machine(
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
    t_dep15 = {
        (m, id_train_dep): model.addVar(vtype=grb.GRB.INTEGER, name="t")
        for m in Taches.TACHES_DEP_MACHINE
        for id_train_dep in liste_id_train_depart
    }
    return t_dep15


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


def init_objectif(
    model: grb.Model,
    is_present: dict,
    liste_id_train_depart: dict,
    temps_min: int,
    temps_max: int,
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
    max_FOR = model.addVar(vtype=grb.GRB.INTEGER, lb=0, name="max_FOR")
    for t in range(temps_min, temps_max + 1):
        model.addConstr(
            max_FOR
            >= grb.quicksum(
                is_present[Chantiers.FOR][(id_train, t)]
                for id_train in liste_id_train_depart
            )
        )
    model.setObjective(max_FOR, grb.GRB.MINIMIZE)

    return True
