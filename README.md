# Optimisation des ressources en gare de triage pour FRET SNCF

## Contributeurs

- Max Arnaud--Vendrell : `max.arnaud-vendrell@student-cs.fr`
- Grégoire Genouville : `gregoire.genouville@student-cs.fr`
- Imanol Lacroix : `imanol.lacroix@student-cs.fr`
- Alexandre Perverie : `alexandre.perverie@student-cs.fr`
- Alexis Prin : `alexis.prin@student-cs.fr`

## Formalisation du problème

On dénote les train d'arrivée par leur identifiant $n_a$, et leurs tâches par un entier $m_a$ qui correspond au numéro de la tâche par ordre chronologique $(m_a=1,2,3)$. On fait de même avec les trains de départ $n_d$ et $m_d$ $(m_d=1,2,3,4)$. Pour $x=a,d$, le temps de réalisation de la tâche $m_x$ est noté $T_{m_x}$. $t_{n_x}^{m_x}$ est le moment auquel on commence la tâche $m_x$ sur le wagon $n_x$. L'heure d'arrivée du train $n_a$ est $t_{n_a}^a$ et l'heure de départ du train $n_d$ est  $t_{n_d}^d$. La durée d'une semaine est $S$ et les heures d'ouverture et de fermeture sont $t_o$ et $t_f$ respectivement. Pour tous les temps, $t=0$ correspond au lundi 8 Août 2022 00:00. Soit 
$$D:n_d\mapsto\{n_a|\text{wagon}(n_a)\cap\text{wagon}(n_d)\neq \empty\}$$
Concrètement, $D$ est un dictionnaire dont les clés sont les identifiants des trains de départ et renvoit la liste des trains d'arrivée qui ont des wagons de ce train de départ.

Les contraintes sont ainsi formalisées :
- Les tâches ne peuvent êtres faites en même temps sur un train : $\forall n_a, \forall m_a \in \llbracket 1,2\rrbracket,t_{n_a}^{m_a}+T^a_{m_a}\leq t_{n_a}^{m_a+1}$ et $\forall n_d, \forall m_d \in \llbracket 1,3\rrbracket,t_{n_d}^{m_d}+T^d_{m_d}\leq t_{n_d}^{m_d+1}$
- La première tâche ne peut être réalisée avant l'arrivée du train : $\forall n_a, t_{n_a}^1\geq t_{n_a}^a$
- La dernière tâche doit se finir avant le départ du train : $\forall n_d, t_{n_d}^4+T^d_4\leq t_{n_d}^d$
- On ne peut commencer la première tâche d'un train de départ si on n'a pas fini la dernière tâche sur tous les trains d'arrivée contenant des wagons du train de départ : $\forall n_d, \forall n_a\in D[n_d], t^1_{n_d}\geq t^4_{n_a}+T^a_4$
- Les tâches nécessitant une machine $(m_a=3$ et $m_d=2,3)$, ne peuvent être réalisées en même temps pour deux wagons : $\forall n_{x1}\neq n_{x2},\left[t_{n_{x1}}^m,t_{n_{x1}}^m+T^x_m\right]\cap\left [t_{n_{x2}}^m,t_{n_{x2}}^m+T^x_m\right]=\empty$ ce qui est reformulé comme $\forall n_{n_{x1}}, \forall n_{n_{x2}}\neq n_{n_{x1}}, t_{n_{x1}}^m\geq t_{n_{x2}}^m+T_m^x \vee t_{n_{x2}}^m\geq t_{n_{x1}}^m+T_m^x$
- Les machines et le chantier de formation doivent être inactif sur leurs créneaux de fermeture : $\forall k =0,1,\forall m_a=3, m_d\in\llbracket 1,3 \rrbracket, \forall n_x, \left[t_{n_x}^m,t_{n_x}^m+T^x_m\right]\cap\left [t_o + kS,t_f+ kS\right]=\empty$