from init_constraint import *

# -- Choix d'un paramétrage d'affichage minimaliste --
model.params.outputflag = 0  # mode muet
# -- Mise à jour du modèle  --
model.update()
# -- Résolution --
model.optimize()

if model.status == GRB.INFEASIBLE:
    print("Le modèle n'a pas de solution")
elif model.status == GRB.UNBOUNDED:
    print("Le modèle est non borné")
else:
    print("Ca marche Bébou")
