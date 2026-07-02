Nous avons pu nous rendre compte des défis logistics d'un centre de bus RATP par la présentation de notre encadrant qui travaille sur des outils IA et par notre rencontre avec Clement Osini directeur performance de l'offre qui à pour role de panifier les routes de bus et de les attitrer aux machinistes ( chauffeurs).
Pour l'instant tout passe par le logiciel cleo. Il permet de visulaiser tous les ervices à pourvoirs et toutes les disponibilités/performances des chauffeurs mais c'est en relaité un regroupement de fichiers excel améliroé et la tâche de planification reste manuelle. Cleo est jugé operationnel à 60-70% et laisse un gap d'optimisation de 50 %
C'est une tache colossale par le nombre de services a distribuer et par le nombre de contraintes de la part des chauffeurs.
La tache est particulièrement difficle car il faut gérer des facteurs humains avec beaucoup d'incertitude, cela rend la planification a long terme presque impossible. Pour l'instant le centre pleyel peut donner aux chauffeurs leurs emlploi du temps d'un mois et demi ce qui est deja tres élévé.

C'est pour cela qu'il est important de developper des outils qui d'abord facilitent la tache du planificateur meme si on ne fournit pas directement un emploi du temps optimisé. On a donc d'abord travaillé sur un agent IA qui lui permet de trouver facilement les informations de chaque service/chauffeur et de limiter le temps de recherche. 

Lorsque nous avons parlé avec le planificateur d'un locigiciel d'optimisation centralisé il n'etait pas convaincu car il veut pourvoir garder le coté humain et de pouvoir modifier en permanence si necessaire, ils ont un logiciel ALF dont la deuxieme version prend bien en compte le fait de servir les preferences des chauffeurs mais ils ne l'utilisent pas et n'en semble pas satisfait.

Nous avons reflechi au problème d'optimisation sour la forme d'un PLNE ( problème linéaire en nombre entier). En fonction des facteurs de decisions on pondère l'affectaion d'un chauffeur à un service puis on essaye de maximiser la somme des poids sur l'ensemble du planning. Les varaibles sont binaires et renvoie 1 si les ervice est assigné et 0 sinon.

