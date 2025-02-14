# Optimisation des ressources en gare de triage pour FRET SNCF

## Contributeurs

- Max Arnaud--Vendrell : `max.arnaud-vendrell@student-cs.fr`
- Grégoire Genouville : `gregoire.genouville@student-cs.fr`
- Imanol Lacroix : `imanol.lacroix@student-cs.fr`
- Alexandre Perverie : `alexandre.perverie@student-cs.fr`
- Alexis Prin : `alexis.prin@student-cs.fr`

## Formalisation du problème

On dénote les wagons  par leur identifiant $i$, et les tâches par un entier $m$ qui correspond au numéro de la tâche par ordre chronologique $(m=1,...,7)$. Le temps de réalisation de la tâche $m$ est noté $T_m$. $t_i^m$ est le moment auquel on commence la tâche $m$ sur le wagon $i$. Les heures d'arrivée et de départ du train du wagons $i$ sont respectivement $t_i^d$ et $t_i^a$. La durée d'une semaine est $S$ et les heures d'ouverture et de fermeture sont $t_o$ et $t_f$ respectivement.

Les contraintes sont ainsi formalisées :
- Les tâches ne peuvent êtres faites en même temps : $\forall m, \forall i, \in \llbracket 1,...,6\rrbracket,t_i^m+T_m\leq t_i^{m+1}$
- La première tâche ne peut être réalisée avant l'arrivée du wagon : $\forall i, t_i^1\geq t_i^a$
- La dernière tâche doit se finir avant le départ du wagon : $\forall i, t_i^7+T_7\leq t_i^d$
- Les tâches nécessitant une machine $(m \in \{3,5,6\})$, ne peuvent être réalisées en même temps pour deux wagons : $\forall i\neq j,\left[t_i^m,t_i^m+T_m\right]\cap\left [t_j^m,t_j^m+T_m\right]=\empty$ 
- Si $\exist k \in \mathbb{Z},\left[t_i^a,t_i^d\right]\cap\left[t_o + kS,t_f+ kS\right]\neq \empty$, alors $\forall m \in \llbracket 3,6 \rrbracket, \forall i, \left[t_i^m,t_i^m+T_m\right]\cap\left [t_o + kS,t_f+ kS\right]=\empty$