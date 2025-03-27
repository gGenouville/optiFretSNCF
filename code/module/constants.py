"""constants n shit"""

import pandas as pd


class Constantes:
    """


    #-------- ne devrait bientot plus être utilisé --------#


    Constantes utilisées dans le module.

    Attributs :
    -----------
    BASE_TIME : pd.Timestamp
        Date de référence pour les calculs temporels.
    """

    BASE_TIME = pd.Timestamp("2022-08-08 00:00")


class Machines:
    """
    Identifiants des machines utilisées dans les opérations.

    Attributs :
    -----------
    DEB : str
        Identifiant pour les machines de début.
    FOR : str
        Identifiant pour les machines de formation.
    DEG : str
        Identifiant pour les machines de dégagement.
    """

    DEB = "DEB"
    FOR = "FOR"
    DEG = "DEG"


class Chantiers:
    """
    Identifiants des chantiers dans les opérations.

    Attributs :
    -----------
    REC : str
        Identifiant pour les chantiers de réception.
    FOR : str
        Identifiant pour les chantiers de formation.
    DEP : str
        Identifiant pour les chantiers de départ.
    """

    REC = "REC"
    FOR = "FOR"
    DEP = "DEP"


class Feuilles:
    """
    Noms des feuilles de calcul Excel utilisées.

    Attributs :
    -----------
    SILLONS_ARRIVEE : str
        Nom de la feuille des sillons d'arrivée.
    SILLONS_DEPART : str
        Nom de la feuille des sillons de départ.
    MACHINES : str
        Nom de la feuille des machines.
    CHANTIERS : str
        Nom de la feuille des chantiers.
    CORRESPONDANCES : str
        Nom de la feuille des correspondances.
    """

    SILLONS_ARRIVEE = "Sillons arrivee"
    SILLONS_DEPART = "Sillons depart"
    MACHINES = "Machines"
    CHANTIERS = "Chantiers"
    CORRESPONDANCES = "Correspondances"
    ROULEMENT_AGENTS = "Roulements agents"
    TACHES_HUMAINES = "Taches humaines"


class Colonnes:
    """
    Noms des colonnes dans les tables de données.

    Attributs :
    -----------
    SILLON_JARR : str
        Colonne du jour d'arrivée.
    SILLON_HARR : str
        Colonne de l'heure d'arrivée.
    SILLON_JDEP : str
        Colonne du jour de départ.
    SILLON_HDEP : str
        Colonne de l'heure de départ.
    SILLON_NUM_TRAIN : str
        Colonne du numéro de train.
    N_TRAIN_ARRIVEE : str
        Colonne du numéro de train d'arrivée.
    N_TRAIN_DEPART : str
        Colonne du numéro de train de départ.
    ID_TRAIN_DEPART : str
        Colonne de l'ID du train de départ.
    ID_TRAIN_ARRIVEE : str
        Colonne de l'ID du train d'arrivée.
    DATE_ARRIVEE : str
        Colonne de la date d'arrivée.
    DATE_DEPART : str
        Colonne de la date de départ.
    ID_WAGON : str
        Colonne de l'ID du wagon.
    INDISPONIBILITE : str
        Colonne des indisponibilités.
    INDISPONIBILITE_MINUTES : str
        Colonne des indisponibilités en minutes.
    """

    SILLON_JARR = "JARR"
    SILLON_HARR = "HARR"
    SILLON_JDEP = "JDEP"
    SILLON_HDEP = "HDEP"
    SILLON_NUM_TRAIN = "n°TRAIN"

    N_TRAIN_ARRIVEE = "n°Train arrivee"
    N_TRAIN_DEPART = "n°Train depart"
    ID_TRAIN_DEPART = "ID Train départ"
    ID_TRAIN_ARRIVEE = "ID Train arrivée"
    DATE_ARRIVEE = "Jour arrivee"
    DATE_DEPART = "Jour depart"
    ID_WAGON = "Id wagon"
    NOMBRE_VOIES = "Nombre de voies"

    INDISPONIBILITE = "Indisponibilites"
    INDISPONIBILITE_MINUTES = "Indisponibilites etendues en minutes"

    ROULEMENT = "Roulement"
    NOMBRE_AGENTS = "Nombre agents"
    CONNAISSANCES_CHANTIERS = "Connaissances chantiers"


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
