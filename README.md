# Optimisation des ressources en gare de triage pour FRET SNCF

## Description

Ce projet utilise le solveur d'optimisation Gurobi optimiser la planification de tâches dans une gare de triage de fret. Le projet est structuré en deux parties principales : le code source et un notebook Jupyter pour l'analyse des résultats.

## Structure du projet

Le projet est organisé comme suit :

    /Jalon 2
    │
    ├── /Code
    │   ├── /modules
    |   |   ├── init.py # Permet de transformer le répertoire en package Python
    │   │   ├── utils2.py               # Fonctions utilitaires pour la préparation et le traitement des données
    │   │   ├── modele2.py              # Fonctions liées à la création et à la gestion du modèle Gurobi
    │   │   ├── contraintes2.py         # Fonctions liées à la création des contraintes du modèle Gurobi
    │   │   └── visualisation2.py       # Fonctions liées à la visualisation des données
    │   │
    │   └── /notebooks
    │       └── Code_jalon_2.ipynb  # Notebook Jupyter pour exécuter le modèle et visualiser les résultats
    │
    └── README.md                # Ce fichier

## Détails des répertoires

### 1. `/Code/modules`

Ce répertoire contient le code Python qui permet d'initialiser le modèle d'optimisation et de définir les fonctions nécessaires pour résoudre le problème. Il comprend les fichiers suivants :

- `__init__.py` : Ce fichier permet à Python de traiter le répertoire /modules comme un package, ce qui facilite l'importation des fonctions et classes définies dans les autres fichiers du répertoire.
  
- `utils2.py` : Ce fichier contient des fonctions utilitaires utilisées pour préparer et traiter les données avant de les passer au modèle Gurobi. Par exemple, il peut inclure des fonctions pour la gestion des horaires, des machines, ou des contraintes spécifiques aux trains.
  
- `modele2.py` : Ce fichier contient les fonctions principales liées à la création du modèle Gurobi, l'ajout des variables de décision, des contraintes et la configuration du solveur. Les modèles sont définis pour résoudre des problèmes d'optimisation en utilisant les données traitées dans `utils2.py`.
  
- `contraintes2.py` : Ce fichier contient les fonctions principales liées à la création des contraintes du modèle Gurobi, il est exclusivement utilisé par le module `modele2.py`.
  
- `visualisation2.py` : Ce fichier contient les fonctions permettant de visualiser les solutions obtenues après optimisation du problème à l'aide des pics d'occupation et de diagramme de Gantt.

### 2. `/Code/notebooks`

Ce répertoire contient les notebooks Jupyter permettant d'exécuter le modèle et d'analyser les résultats ainsi que les données fournies. Il contient actuellement un fichier  produit:

- `Code_jalon_2.ipynb` : Ce notebook Jupyter est destiné à être exécuté pour obtenir les résultats du deuxième jalon. Vous pouvez simplement exécuter le notebook en utilisant Run All une fois les dépendances installées pour visualiser les résultats d'optimisation et d'analyse.

## Lancer l'analyse

Ouvrez le fichier `Code_jalon_2.ipynb` et exécutez toutes les cellules en cliquant sur Run All.

Une fois le notebook ouvert, le modèle sera initialisé et les différentes étapes d'optimisation seront exécutées. Vous pourrez visualiser les résultats dans les cellules suivantes, et analyser les horaires optimaux des trains ainsi que les contraintes respectées par le modèle dans un diagramme de Gante.

## Contributeurs

- Max Arnaud--Vendrell : `max.arnaud-vendrell@student-cs.fr`
- Grégoire Genouville : `gregoire.genouville@student-cs.fr`
- Imanol Lacroix : `imanol.lacroix@student-cs.fr`
- Alexandre Perverie : `alexandre.perverie@student-cs.fr`
- Alexis Prin : `alexis.prin@student-cs.fr`