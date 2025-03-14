# Optimisation des ressources en gare de triage pour FRET SNCF

## Contributeurs

- Max Arnaud--Vendrell : `max.arnaud-vendrell@student-cs.fr`
- Grégoire Genouville : `gregoire.genouville@student-cs.fr`
- Imanol Lacroix : `imanol.lacroix@student-cs.fr`
- Alexandre Perverie : `alexandre.perverie@student-cs.fr`
- Alexis Prin : `alexis.prin@student-cs.fr`

## Formalisation du problème

Nous définissons les variables et les contraintes comme suit avec $x=a$ pour les train d'arrivée et $x=d$ pour les trains de départs :

### Données d'entrée


* $T_x[m]$ : Durée de la tâche $m$.
* $t_x[n]$ : Heures d'arrivée et de départ des trains (en fonction de si le train est de départ ou d'arrivée).
* $D[n]$ : Liste des trains d'arrivée ayant des wagons composant le train de départ $n$.
* $L_{mach}[m]$ la liste des heures d'ouverture et de fermetures des machines $m \in\{DEB, FOR, REG\}$. Un créneau est de la forme $I_{mach}[m,i]=[L_{mach}[m,2i],L_{mach}[m,2i+1]]$
* $L_{chan}[c]$ l'équivalent de $L_{mach}$ pour les chantiers $c$, avec $I_{chan}[c,i]=[L_{chan}[c,2i],L_{chan}[c,2i+1]]$.

### Variables de décision
* $t_x[n,m]$ : Heure de début de la tâche $m$ pour le train $n$.
* $t_{x,mach}[n,m]$ : Heure de d\'ebut de la t\^ache machine $m\in\{DEB, FOR, DEG\}$ pour le train $n$, comptée en quarts d'heure.
* $\delta_x[m,n_1,n_2]$ : Variable binaire qui vaut 1 si le train $n_1$ passe avant le train $n_2$ pour la tache $m$ et sinon 0, défini pour toutes les tâches machines ($m \in \{DEB, FOR, DEG\}$).
* $\delta_{mach}[m,n,i]$ : Variable binaire qui vaut 1 si le train $n$ passe entre les intervalles de fermeture $I_{mach}[i-1]$ et $I_{mach}[i]$ pour la tache $m$ et sinon 0, défini pour toutes les tâches machines ($m \in \{DEB, FOR, DEG\}$).
* $\delta_{chan}[c,m,n,i]$ : Variable binaire qui vaut 1 si le train $n$ passe entre les intervalles de fermeture $I_{chan}[c,i-1]$ et $I_{chan}[c,i]$ pour la tache $m \in c$ et sinon 0, défini pour toutes les chantiers ($c \in \{REC, FOR, DEP\}$).

### Contraintes
Nous avons choisi une modélisation où :
* Les tâches machines doivent commencer en début de quart d'heure :
$$\forall n,\forall m\in\{DEB, FOR, DEG\}, t_x[n,m]=15 t_{x,mach}[n,m]$$
* Respect de l'ordre des tâches :
$$ \forall n_a, \forall m_a \in \llbracket 1,2\rrbracket, t_{n_a}^{m_a} + T^a_{m_a} \leq t_{n_a}^{m_a+1}$$ 
$$\forall n_d, \forall m_d \in \llbracket 1,3\rrbracket, t_{n_d}^{m_d} + T^d_{m_d} \leq t_{n_d}^{m_d+1}$$
\end{equation}
* Pas de tâche avant l'arrivée du train $n_a$ :
$$\forall n_a, t_{n_a}^1 \geq t_{n_a}^a$$
* Fin des tâches avant le départ du train $n_d$ :
$$\forall n_d, t_{n_d}^4 + T^d_4 \leq t_{n_d}^d$$
* Précédence des tâches entre trains connectés :
$$\forall n_d, \forall n_a \in D[n_d], t^1_{n_d} \geq t^4_{n_a} + T^a_4$$
* Les tâches nécessitant une machine sont modélisées en respectant des contraintes d'exclusion mutuelle, ce qui garantit qu'une machine ne peut pas être utilisée par plusieurs tâches simultanément.
$$\forall n_{1} \neq n_{2}, \underbrace{\left( t_x[{n_{1}},m] \geq t_x[{n_{2}},m] + T_x[m] \right)}_{\substack{\text{la fin de la tâche sur } n_{1}\\ \text{est avant la fin de la tâche}\\\text{sur } n_{2}}} \vee \left( t_x[{n_{2}},m] \geq t_x[{n_{1}},m] + T_x[m] \right)$$
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Pour la linéarisation nous avons reformulé la contrainte en deux &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;contraintes:
$$\forall n_{1} \neq n_{2}, 
\begin{cases}
    t_x[{n_{2}},m]+ T_x[m] \leq t_x[{n_{1}},m] + (1-\delta_x[m,n_1,n_2])\times M_{big}\\
    t_x[{n_{1}},m]+ T_x[m] \leq t_a[{n_{2}},m] -\delta_x[m,n_1,n_2]\times M_{big}
\end{cases}$$
* Les contraintes horaires d'indisponibilité des machines sont imposées pour assurer que les tâches machines s'insèrent dans les créneaux disponibles. Les contraintes suivantes assurent la cohérences entre les variables $t_x[m,n]$ et $\delta_{mach}[m,n,i]$ :
$$\begin{split}
    &\forall m \in \{DEB, FOR, DEG\}, \forall n, \forall i,\\ &\begin{cases}
        t_x[n,m]\geq L_{mach}[m,2i-1] -(1- \delta_{mach}[m,n,i])\times M_{big}\\
        t_x[n,m]\leq L_{mach}[m,2i]-T_x[m] +(1- \delta_{mach}[m,n,i])\times M_{big}
    \end{cases}
    \end{split}$$
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Étant donné qu'une tâche ne peut être que dans un seul &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;intervalle d'ouverture à la fois, on impose
$$\forall m \in \{DEB, FOR, DEG\}, \forall n, \sum_i \delta_{mach}[m,n,i]=1$$

* Les contraintes horaires d'ouverture et de fermeture des chantiers sont imposées pour assurer que toutes les tâches du chantier s'insèrent dans les créneaux disponibles. Les contraintes suivantes assurent la cohérences entre les variables $t_x[m,n]$ et $\delta_{chan}[m,n,i]$
$$\begin{split}
    &\forall c\in \{REC, FOR, DEP\},\forall m \in c, \forall n, \forall i,\\ &\begin{cases}
        t_x[n,m]\geq L_{chan}[c,2i-1] -(1- \delta_{chan}[c,m,n,i])\times M_{big}\\
        t_x[n,m]\leq L_{chan}[c,2i]-T_x[m] +(1- \delta_{chan}[c,m,n,i])\times M_{big}
    \end{cases}
    \end{split}$$
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Étant donné qu'une tâche ne peut être que dans un seul &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;intervalle d'ouverture à la fois, on impose
$$\forall c\in \{REC, FOR, DEP\},\forall m \in c, \forall n, \sum_i \delta_{chan}[c,m,n,i]=1$$