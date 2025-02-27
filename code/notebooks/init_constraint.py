from gurobipy import *
from creation_dictionnaires import *

# Charger le fichier Excel
file = "instance_WPY_realiste_jalon1.xlsx"

t_a, t_d = creation_listes_temps_arrivee_depart(file)


model = Model("SNCF JALON 1")

M_arr = 3  # Nombre de tâches à effectuer sur chaque train d'arrivée
M_dep = 4  # Nombre de tâches à effectuer sur chaque train de départ
S = 60*24*7     # Nombre de minutes dans une semaine

liste_id_train_arrivee = t_a.keys()
liste_id_train_depart = t_d.keys()

taches_arrivee = [1, 2, 3]
taches_depart = [1, 2, 3, 4]

# Temps de début de la tâche m sur le train d'arrivée n, en minute, comptée à partir du lundi 8 Aout 2022 00:00
t_arr = {(m, id_train_arr): model.addVar(vtype=GRB.INTEGER, name="t")
         for m in taches_arrivee for id_train_arr in liste_id_train_arrivee}

# Temps de début de la tâche m sur le train de départ n, en minute, comptée à partir du lundi 8 Aout 2022 00:00
t_dep = {(m, id_train_dep): model.addVar(vtype=GRB.INTEGER, name="t")
         for m in taches_depart for id_train_dep in liste_id_train_depart}

T_arr = {1: 15, 2: 45, 3: 15}       # Durée des tâches sur les trains d'arrivée
# Durée des tâches sur les trains de départ
T_dep = {1: 15, 2: 150, 3: 15, 4: 20}


def init_constraint(model):
    for id_train_arr in liste_id_train_arrivee:
        model.addConstr(t_arr[(1, id_train_arr)] >= t_a[id_train_arr])
        for m in taches_arrivee[:-1]:
            model.addConstr(t_arr[(m, id_train_arr)] +
                            T_arr[m] <= t_arr[(m+1, id_train_arr)])

    for id_train_dep in liste_id_train_depart:
        M_dep = taches_depart[-1]
        model.addConstr(t_dep[(M_dep, id_train_dep)] +
                        T_dep[M_dep] <= t_d[id_train_dep])
        for m in taches_depart[:-1]:
            model.addConstr(t_dep[(m, id_train_dep)] +
                            T_dep[m] <= t_dep[(m+1, id_train_dep)])

    M_big = 100000

    for id_arr_1 in liste_id_train_arrivee:
        for id_arr_2 in liste_id_train_arrivee:
            if id_arr_1 != id_arr_2:
                delta = model.addVar(
                    vtype=GRB.BINARY, name=f"delta_arr_{id_arr_1}_{id_arr_2}")

                # Si delta = 1, alors id_arr_2 se termine avant id_arr_1
                model.addConstr(t_arr[(3, id_arr_2)] + T_arr[3]
                                <= t_arr[(3, id_arr_1)] + (1 - delta) * M_big)

                # Si delta = 0, alors id_arr_1 se termine avant id_arr_2
                model.addConstr(t_arr[(3, id_arr_2)] >= t_arr[(
                    3, id_arr_1)] + T_arr[3] - delta * M_big)

    for m_dep in [1, 3]:
        for id_dep_1 in liste_id_train_depart:
            for id_dep_2 in liste_id_train_depart:
                if id_dep_1 != id_dep_2:
                    delta = model.addVar(
                        vtype=GRB.BINARY, name=f"delta_dep_{m_dep}_{id_dep_1}_{id_dep_2}")

                    # Si delta = 1, alors id_dep_2 se termine avant id_dep_1
                    model.addConstr(t_dep[(m_dep, id_dep_2)] + T_dep[m_dep]
                                    <= t_dep[(m_dep, id_dep_1)] + (1 - delta) * M_big)

                    # Si delta = 0, alors id_dep_1 se termine avant id_dep_2
                    model.addConstr(t_dep[(m_dep, id_dep_2)] >= t_dep[(
                        m_dep, id_dep_1)] + T_dep[m_dep] - delta * M_big)

    # Horaires limites de la disponibilité du chantier de formation et des machines (en minutes)
    Limites = np.array([5, 13, 5*24+13, 5*24+21, 6*24 +
                       13, 6*24+21, 7*24+5, 7*24+13])*60

    M_big = 100000  # Une grande constante, à ajuster en fonction de tes données

    for id_arr in liste_id_train_arrivee:
        delta = model.addVars(5, vtype=GRB.BINARY,
                              name=f"delta_arr_{id_arr}")  # 5 cas possibles

        # Cas 1 : Avant la première limite
        model.addConstr(t_arr[(3, id_arr)] <= Limites[0] -
                        T_arr[3] + (1 - delta[0]) * M_big)

        # Cas 2 : Entre Limites[1] et Limites[2]
        model.addConstr(t_arr[(3, id_arr)] >= Limites[1] -
                        delta[1] * M_big)  # Limite inf
        model.addConstr(t_arr[(3, id_arr)] <= Limites[2] -
                        T_arr[3] + (1 - delta[1]) * M_big)  # Limite sup

        # Cas 3 : Entre Limites[3] et Limites[4]
        model.addConstr(t_arr[(3, id_arr)] >= Limites[3] -
                        delta[2] * M_big)  # Limite inf
        model.addConstr(t_arr[(3, id_arr)] <= Limites[4] -
                        T_arr[3] + (1 - delta[2]) * M_big)  # Limite sup

        # Cas 4 : Entre Limites[5] et Limites[6]
        model.addConstr(t_arr[(3, id_arr)] >= Limites[5] -
                        delta[3] * M_big)  # Limite inf
        model.addConstr(t_arr[(3, id_arr)] <= Limites[6] -
                        T_arr[3] + (1 - delta[3]) * M_big)  # Limite sup

        # Cas 5 : Après la dernière limite
        model.addConstr(t_arr[(3, id_arr)] >= Limites[7] - delta[4] * M_big)

        # Une seule de ces conditions peut être vraie
        model.addConstr(delta[0] + delta[1] +
                        delta[2] + delta[3] + delta[4] == 1)

    for m_dep in [1, 2, 3]:
        for id_dep in liste_id_train_depart:
            delta = model.addVars(
                # 5 cas possibles
                5, vtype=GRB.BINARY, name=f"delta_dep_{id_dep}")

            # Cas 1 : Avant la première limite
            model.addConstr(
                t_dep[(m_dep, id_dep)] <= Limites[0] - T_dep[m_dep] + (1 - delta[0]) * M_big)

            # Cas 2 : Entre Limites[1] et Limites[2]
            model.addConstr(t_dep[(m_dep, id_dep)] >=
                            Limites[1] - delta[1] * M_big)  # Limite inf
            model.addConstr(t_dep[(m_dep, id_dep)] <= Limites[2] -
                            # Limite sup
                            T_dep[m_dep] + (1 - delta[1]) * M_big)

            # Cas 3 : Entre Limites[3] et Limites[4]
            model.addConstr(t_dep[(m_dep, id_dep)] >=
                            Limites[3] - delta[2] * M_big)  # Limite inf
            model.addConstr(t_dep[(m_dep, id_dep)] <= Limites[4] -
                            # Limite sup
                            T_dep[m_dep] + (1 - delta[2]) * M_big)

            # Cas 4 : Entre Limites[5] et Limites[6]
            model.addConstr(t_dep[(m_dep, id_dep)] >=
                            Limites[5] - delta[3] * M_big)  # Limite inf
            model.addConstr(t_dep[(m_dep, id_dep)] <= Limites[6] -
                            # Limite sup
                            T_dep[m_dep] + (1 - delta[3]) * M_big)

            # Cas 5 : Après la dernière limite
            model.addConstr(t_dep[(m_dep, id_dep)] >=
                            Limites[7] - delta[4] * M_big)

            # Une seule de ces conditions peut être vraie
            model.addConstr(delta[0] + delta[1] +
                            delta[2] + delta[3] + delta[4] == 1)

    for id_dep in liste_id_train_depart:
        for id_arr in D[id_dep]:
            model.addConstr(t_dep[(1, id_dep)] >=
                            t_arr[(3, id_arr)] + T_arr[3])
