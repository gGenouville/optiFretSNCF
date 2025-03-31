# Optimisation des ressources en gare de triage pour FRET SNCF

## Description

Ce projet utilise le solveur d'optimisation Gurobi pour optimiser la planification de tâches dans une gare de triage de fret. Le projet est structuré en deux parties principales : le code source et un notebook Jupyter pour l'analyse des résultats.

## Structure du projet

Le projet est organisé comme suit :

    /Jalon 2
    │
    ├── /Code
    │   ├── /modules
    |   |   ├── init.py # Permet de transformer le répertoire en package Python
    │   │   ├── constantes.py # Contients les divers paramètres (noms des feuilles, colonnes, machines, ...)
    │   │   ├── contraintes.py # Fonctions liées à la création des contraintes du modèle Gurobi
    │   │   ├── modele.py # Fonctions liées à la création et à la gestion du modèle Gurobi
    │   │   ├── parser.py # Ouvre et ecrit les excel(=bloat), creer les variables utiles(t_a, ...)
    │   │   └── visualisation.py # Fonctions liées à la visualisation des données
    │   │
    │   └── /notebooks
    │       └── A_executer.ipynb # Notebook Jupyter pour exécuter le modèle et visualiser les résultats
    │
    └── README.md # Ce fichier

## Lancer l'analyse

Ouvrez le fichier `A_executer.ipynb` et exécutez toutes les cellules en cliquant sur Run All.

Une fois le notebook ouvert, le modèle sera initialisé et les différentes étapes d'optimisation seront exécutées. Vous pourrez visualiser les résultats dans les cellules suivantes, et analyser les horaires optimaux des trains ainsi que les contraintes respectées par le modèle dans un diagramme de Gante. Par défaut le notebook utilise l'instance simple. 

## Contributeurs

- Max Arnaud--Vendrell : `max.arnaud-vendrell@student-cs.fr`
- Grégoire Genouville : `gregoire.genouville@student-cs.fr`
- Imanol Lacroix : `imanol.lacroix@student-cs.fr`
- Alexandre Perverie : `alexandre.perverie@student-cs.fr`
- Alexis Prin : `alexis.prin@student-cs.fr`
