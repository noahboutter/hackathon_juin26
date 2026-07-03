# Hackathon Juin 2026 - Optimisation de la Planification RATP (Centre Pleyel)

## Notre démarche et immersion métier
Notre projet a débuté par une compréhension concrète des défis logistiques d'un centre de bus RATP. Nous avons été guidés par notre encadrant Arnaud Techer(Responsable Programme IA Ops) et par notre rencontre avec Clément Osini, directeur performance de l'offre, dont le rôle est de planifier les routes de bus et de les attitrer aux machinistes (chauffeurs) lors d'une visite du centre bus de Pleyel.

Nous avons pu analyser les outils actuellement en place :
- **Le logiciel Cleo :** Actuellement, tout passe par ce logiciel. S'il permet de visualiser tous les services à pourvoir ainsi que les disponibilités et performances des chauffeurs, il s'agit en réalité d'un regroupement de fichiers Excel amélioré. La tâche de planification reste entièrement manuelle. Cleo est jugé opérationnel à 60-70%, ce qui laisse un gap d'optimisation massif de 50%.
- **Le logiciel ALF (V2) :** La RATP possède cet autre logiciel qui prend bien en compte le fait de servir les préférences des chauffeurs, mais les planificateurs ne l'utilisent pas et n'en semblent pas satisfaits.
- **La réticence à l'automatisation totale :** En discutant avec le planificateur d'un potentiel logiciel d'optimisation centralisé, celui-ci n'était pas convaincu. Son besoin principal est de garder la mainmise (le côté humain) et de pouvoir modifier les plannings en temps réel si nécessaire.

## Difficultés rencontrées
Le problème de planification RATP est particulièrement complexe pour plusieurs raisons :
1. **La dimension colossale de la tâche :** Le volume énorme de services à distribuer croisé avec le grand nombre de contraintes émanant des chauffeurs et de la legislation.
2. **Le facteur humain et l'incertitude :** Ces paramètres rendent la planification à long terme presque impossible. À l'heure actuelle, le centre Pleyel que nous avons visité parvient à donner aux chauffeurs leur emploi du temps un mois et demi à l'avance, ce qui est déjà considéré comme un délai très élevé, dans d'autres centres bus le maximum est de deux semaines.

## Solutions trouvées et Valeur ajoutée
Face au refus d'un outil d'optimisation "boîte noire" qui remplacerait l'humain, nous avons pivoté vers des outils qui **facilitent** la tâche du planificateur sans lui imposer directement un emploi du temps figé.

### 1. Un Agent IA de recherche intuitive
Nous avons d'abord travaillé sur un agent IA conçu pour permettre au planificateur de trouver facilement les informations de chaque service ou chauffeur et de limiter son temps de recherche. 
- **Fonctionnement :** L'agent est capable d'interpréter des questions posées en langage humain.
- **Implémentation :** Ces requêtes en langage naturel sont associées à une dizaine de fonctions de filtres spécifiques que nous avons développées.

### 2. Modélisation mathématique de l'optimisation (PLNE)
En parallèle, nous avons réfléchi au problème d'optimisation de manière formelle sous la forme d'un **PLNE (Problème Linéaire en Nombres Entiers)** avec Sophie Demassey, chercheuse au CMA des Mines de Paris :
- En fonction des facteurs de décision, nous pondérons l'affectation d'un chauffeur à un service.
- L'algorithme essaie ensuite de maximiser la somme de ces poids sur l'ensemble du planning.
- **Variables :** Les variables de ce problème sont binaires (elles renvoient 1 si le service est assigné au chauffeur, et 0 sinon).

## Choix techniques
- **Agent IA & NLP :** Traduction des questions en langage naturel vers nos fonctions de filtres.
- **Modélisation Algorithmique :** Formulation du problème sous forme de PLNE avec optimisation de variables binaires.
- **Interface Streamlit :** Pour exploiter facilement les outils que nous avons développé.

## Notre organisation
- Un groupe de 2 pour la partie LLM
- Un groupe de 2 pour la partie Optimisation
- Une personne pour l'interface Streamlit

## Ce que nous aurions fait différemment avec plus de temps
- Comme beaucoup de choses ne sont pas standardisées dans les données, il y a encore une partie des exceptions qui n'est pas gérée. 
- Nous n'avons pas pu, dans le temps qui nous était imparti, que notre optimisation était vraiment la meilleure option possible et de confirmer l'efficacité de nos codes.
- Notre agent IA repose sur un modèle local, Ollama 3.1, ce qui limite la rapidité de la réponse de notre chatbot.