# Projet n°9 – RATP Cap : IA pour la planification
Équipe : Adèle ABADA, Paul BEXON, Noah BOUTTER, Isaura DUPONT--BARNICH, Mona SIDHOUM

## Contexte et Objectifs
Le métier de planificateur ("feuilliste") nécessite d'analyser en permanence de multiples données (plannings, contraintes légales, compétences des agents) pour affecter les bons services aux bons conducteurs.

Ce projet vise à faciliter ce processus à travers deux grands axes :

- un **assistant IA** (Chatbot) : permettre au planificateur d'interroger ses données (fichiers Excel) en langage naturel, sans avoir à coder ou manipuler manuellement les tableaux

- un **algorithme d'optimisation** : automatiser l'affectation des services en respectant les contraintes du métier (connaissance de la ligne, temps de repos, etc.)

## Partie 1 : Assistant IA (Chatbot)
L'assistant repose sur une architecture d'Agent ReAct (Raisonnement + Action). Contrairement à un simple LLM qui génère du texte, notre agent dispose d'outils Python (via Pandas) lui permettant d'aller lire, filtrer et croiser les données réelles des fichiers Excel avant de formuler sa réponse.

**Stack technique :**

- Modèle : Llama 3.1 via **Ollama** (modèle local pour garantir la stricte confidentialité des données RH).

- Orchestration : **LangChain** pour lier le LLM aux fonctions d'analyse.

- Interface : **Streamlit** pour une expérience utilisateur fluide.

**Exemples d'utilisation :**

Le planificateur peut poser des questions variées allant de la simple consultation à l'anticipation des risques. Voici quelques exemples :

- Consultation : "Combien y a-t-il de services du matin (MAT) à couvrir ?"

- Recherche précise : "Quels agents peuvent réaliser le service précis L140S006 ?"

- Analyse de crise : "Quelles sont les lignes en pénurie de conducteurs le 12/01 ?"

_Note_ : Une liste exhaustive des questions supportées, ainsi que les réponses attendues pour valider le comportement de l'IA, est disponible dans le fichier de test questions_reponses.xlsx joint à ce dépôt.

**Installation et Exécution :**

1. Prérequis :
- Avoir installé Ollama sur sa machine.
- Avoir téléchargé le modèle utilisé :
```bash
ollama run llama3.1
```

2. Installation des dépendances :
Assurez-vous d'être dans un environnement virtuel Python, puis installez les modules requis via le fichier _requirements.txt_ :

```bash
pip install -r requirements.txt
```


3. Lancement de l'interface utilisateur :
Pour démarrer le chatbot dans votre navigateur, exécutez la commande suivante à la racine du projet :

```bash
streamlit run Partie_1_LLM/interface.py
```
(Vous pouvez également tester la version console en exécutant python Partie_1_LLM/main.py)

## Partie 2 : Algorithme d'Optimisation
L'algorithme calcule ici l'affectation optimale sur l'ensemble du planning, en maximisant la satisfaction des préférences des agents tout en respectant strictement les contraintes de qualification, de disponibilité et de repos.

- Matrice de faisabilité D (initialize_data) : D[i, j] = 1 si le machiniste i peut réaliser le service j, c'est-à-dire s'il connaît la ligne concernée et si son statut du jour (ASSU, DISPO, DISPO AM/M/N, etc.) est compatible avec l'horaire du service.

- Matrice de pondération W (W_initialize) : attribue un score à chaque affectation possible, en fonction du rang de préférence de l'agent pour la ligne et pour le type d'horaire (MAT, AM, JOUR, COUP, NUIT).

- correction_en_fonction_du_jour_d_avant applique les règles de repos : un agent ayant travaillé l'après-midi ou la nuit la veille voit certains créneaux du lendemain bloqués dans D (ex : pas de matin/coupure après une nuit).
-une optimisation de la satisfaction avec les conraintes respectée
- un emploi du temps avec les affectations réalisées

**Stack technique :**
- OR-Tools (solveur SCIP) : résolution du problème d'affectation par optimisation linéaire (pywraplp)
- OpenPyXL : mise à jour du fichier de planning Excel avec coloration conditionnelle des cellules affectées

**Installation et Exécution :**
Placer les fichiers de données requis dans Partie_1_LLM/data/ :
    - Export_Planning_du_12_01_2026_au_16_01_2026.xlsx (planning des machinistes),
    - un fichier Services_Agents_non_affectés_le_JJ_MM_AAAA.xlsx par jour à traiter,
    -preferences_agents.xlsx dans Partie_2_Optimisation/ (préférences de ligne et d'horaire).
    - résolution du problème d'affectation via optimisation.opti ;
    mise à jour du planning Excel via optimisation.update_planning ;