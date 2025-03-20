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
* $L_v[c]$ : nombre de voies pour chaque chantier $c$.

### Variables de décision

* $t_x[n,m]$ : Heure de début de la tâche $m$ pour le train $n$, comptée en quarts d'heure.
* $\delta_x[m,n_1,n_2]$ : Variable binaire qui vaut 1 si le train $n_1$ passe avant le train $n_2$ pour la tache $m$ et sinon 0, défini pour toutes les tâches machines ($m \in \{DEB, FOR, DEG\}$).
* $\delta_{mach}[m,n,i]$ : Variable binaire qui vaut 1 si le train $n$ passe entre les intervalles de fermeture $I_{mach}[i-1]$ et $I_{mach}[i]$ pour la tache $m$ et sinon 0, défini pour toutes les tâches machines ($m \in \{DEB, FOR, DEG\}$).
* $\delta_{chan}[c,m,n,i]$ : Variable binaire qui vaut 1 si le train $n$ passe entre les intervalles de fermeture $I_{chan}[c,i-1]$ et $I_{chan}[c,i]$ pour la tache $m \in c$ et sinon 0, défini pour toutes les chantiers ($c \in \{REC, FOR, DEP\}$).
* $ip[c,n,t_{15}]$ : Variable binaire qui dit si le train $n$ est dans le chantier $c$ au temps $t_{15}$ compté en quinzaine de minute.
* $bub[c,n,t_{15}]$ : Variable binaire qui dit si le train $n$ est entré dans le chantier $c$ au temps $t_{15}$ compté en quinzaine de minute.
* $alb[c,n,t_{15}]$ : Variable binaire qui dit si le train $n$ n'est pas encore sorti du chantier $c$ au temps $t_{15}$ compté en quinzaine de minute.
* $\max_{FOR}$ : Le pic d'utilisation des voies du chantier de formation.
* $pw[n]$: variable qui prend l'heure ou le premier wagon de train de départ $n$ commence sa tâche de débranchement.

### Contraintes

* Respect de l'ordre des tâches :
    $$\forall n, \forall m \in \llbracket 1,2\rrbracket, 15t_a[n,m] + T_a[m] \leq 15t_a[n,m+1]$$
    $$\forall n, \forall m \in \llbracket 1,3\rrbracket, 15t_d[n,m] + T_d[m] \leq 15t_d[n,m+1]$$
* Pas de tâche avant l'arrivée du train $n_a$ :
    $$\forall n, 15t_a[n,1] \geq t_a[n]$$
* Fin des tâches avant le départ du train $n_d$ :
    $$\forall n, 15t_d[n,4] + T_d[4] \leq t_d[n]$$
    
* Précédence des tâches entre trains connectés :
    $$\forall n, \forall n \in D[n_d], 15t_d[n,1] \geq 15t_a[n,4] + T_a[4]$$
* Les tâches nécessitant une machine sont modélisées en respectant des contraintes d'exclusion mutuelle, ce qui garantit qu'une machine ne peut pas être utilisée par plusieurs tâches simultanément.
     $$ \forall n_{1} \neq n_{2}, \underbrace{\left( 15t_x[{n_{1}},m] \geq 15t_x[{n_{2}},m] + T_x[m] \right)}_{\substack{\text{la fin de la tâche sur } n_{1}\text{ est avant la fin de la}\\ \text{tâche sur } n_{2}}}\vee \left( 15t_x[{n_{2}},m] \geq 15t_x[{n_{1}},m] + T_x[m] \right)$$

    Pour la linéarisation nous avons reformulé la contrainte en deux contraintes:

    $$\forall n_{1} \neq n_{2}, 
        \begin{cases}
            15t_x[{n_{2}},m]+ T_x[m] \leq 15t_x[{n_{1}},m] + (1-\delta_x[m,n_1,n_2])\times M_{big}\\
            15t_x[{n_{1}},m]+ T_x[m] \leq 15t_x[{n_{2}},m] -\delta_x[m,n_1,n_2]\times M_{big}
        \end{cases}   $$

* Les contraintes horaires d'indisponibilité des machines sont imposées pour assurer que les tâches machines s'insèrent dans les créneaux disponibles. Les contraintes suivantes assurent la cohérences entre les variables $t_x[m,n]$ et $\delta_{mach}[m,n,i]$ :
     $$\begin{split}
        &\forall m \in \{DEB, FOR, DEG\}, \forall n, \forall i,\\ &\begin{cases}
            15t_x[n,m]\geq L_{mach}[m,2i-1] -(1- \delta_{mach}[m,n,i])\times M_{big}\\
            15t_x[n,m]\leq L_{mach}[m,2i]-T_x[m] +(1- \delta_{mach}[m,n,i])\times M_{big}
        \end{cases}
     \end{split}$$
    Étant donné qu'une tâche ne peut être que dans un seul intervalle d'ouverture à la fois, on impose
    $$\forall m \in \{DEB, FOR, DEG\}, \forall n, \sum_i \delta_{mach}[m,n,i]=1$$

* Les contraintes horaires d'ouverture et de fermeture des chantiers sont imposées pour assurer que toutes les tâches du chantier s'insèrent dans les créneaux disponibles. Les contraintes suivantes assurent la cohérences entre les variables $t_x[m,n]$ et $\delta_{chan}[m,n,i]$
     $$\begin{split}
        &\forall c\in \{REC, FOR, DEP\},\forall m \in c, \forall n, \forall i,\\ &\begin{cases}
            15t_x[n,m]\geq L_{chan}[c,2i-1] -(1- \delta_{chan}[c,m,n,i])\times M_{big}\\
            15t_x[n,m]\leq L_{chan}[c,2i]-T_x[m] +(1- \delta_{chan}[c,m,n,i])\times M_{big}
        \end{cases}
     \end{split}$$
    Étant donné qu'une tâche ne peut être que dans un seul intervalle d'ouverture à la fois, on impose
    $$\forall c\in \{REC, FOR, DEP\},\forall m \in c, \forall n, \sum_i \delta_{chan}[c,m,n,i]=1$$

* Les contraintes de l'indicateur d'occupations sont : 
    $$ip[c,n,t_{15}]=bub[c,n,t_{15}]\wedge alb[c,n,t_{15}]$$
    * Pour le chantier de réception, l'entrée est à l'arrivée du train et la sortie et à la fin de la tâche de débranchement.
        $$\begin{cases}
                15t_{15} \geq t_a[n] - M_{big} \times (1 -alb[REC,n,t_{15}])\\
                15t_{15}\leq t_a[n]-\varepsilon+M_{big} \times alb[REC,n,t_{15}]\\
                15t_{15} \leq 15t_a[n,3]+T_a[3] + M_{big} \times (1 -bub[REC,n,t_{15}])\\
                15t_{15}\geq 15t_a[n,3]+T_a[3]+\varepsilon-M_{big} \times bub[REC,n,t_{15}]
            \end{cases}$$
    * Pour le chantier de formation, l'entrée est au début de la tâche de formation (appui voie et mise en place des cales) et la sortie et à la fin de la tâche de dégarage.
        $$    \begin{cases}
                15t_{15} \geq 15t_d[n,1] - M_{big} \times (1 -alb[FOR,n,t_{15}])\\
                15t_{15}\leq 15t_d[n,1]-\varepsilon+M_{big} \times alb[FOR,n,t_{15}]\\
                15t_{15} \leq 15t_d[n,3]+T_d[3] + M_{big} \times (1 -bub[FOR,n,t_{15}])\\
                15t_{15}\geq 15t_d[n,3]+T_d[3]+\varepsilon-M_{big} \times bub[FOR,n,t_{15}]
            \end{cases}$$
    * Pour le chantier de départ, l'entrée est au début de la tâche de dégarage et la sortie et au départ du train.
        $$    \begin{cases}
                15t_{15} \geq 15t_d[n,3]+T_d[3]+\varepsilon - M_{big} \times (1 -alb[DEB,n,t_{15}])\\
                15t_{15}\leq 15t_d[n,3]+T_d[3]+M_{big} \times alb[DEB,n,t_{15}]\\
                15t_{15} \leq t_d[n] + M_{big} \times (1 -bub[DEB,n,t_{15}])\\
                15t_{15}\geq t_d[n]+\varepsilon-M_{big} \times bub[DEB,n,t_{15}]
            \end{cases}$$
* Les voies des chantiers ne peuvent être saturées :
    $$\forall c,\forall t, \sum_n ip[c,n,t]\leq L_v(c)$$
* La contrainte sur le pic du chantier de formation est :
    $$\forall t,\sum_n ip[FOR,n,t]\leq\max_{FOR}$$
* La contrainte pour l'heure du premier wagon qui est sur le chantier de formation du train de départ $$n$$, soit quand un wagon du train $$n$$ commence la tâche de débranchement.
  $$pw[n]= \min_{n' \in D[n]} 15t_a[n,3]$$

### Fonction objectif

Le problème est formulé ainsi :
$$\min \max_{FOR}$$

Cette modélisation correspond à une optimisation min-max classique.
