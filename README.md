# Projet n°9 – RATP Cap : IA pour la planification

Adèle ABADA, Paul BEXON, Noah BOUTTER, Isaura DUPONT--BARNICH, Mona SIDHOUM

## Objectifs

1. Coder une IA de type chatbot pour qu'un planificateur n'aie qu'à poser des questions en français et lire les réponses de l'IA, plutôt que d'aller chercher lui-même dans les bases de données. Par exemple :

```bash
>>> Combien y a-t-il d'agents disponibles pour conduire la ligne 66 le 12/01 au matin ?

Il y en a 115.
```

2. Coder un algorithme d'optimisation pour affecter les services.

## Outils

Pour coder l'IA générative, nous utilisons Ollama avec le modèle `llama3.1`, qui est un petit modèle local.

## 1. Chatbot

Le chatbot est apte à répondre aux types de questions suivantes :
- Combien y a-t-il de services du matin à affecter ?
- Quels sont les services que l'agent 149 peut réaliser ?
- Quels sont les agents disponibles pour le service L140S006 ?
- Quelles sont les lignes connues par l'agent 458 ?
- Quels services sont pour l'instant affectés à l'agent 389 ?
- Combien de services n'ont pas été affectés ?

### Interface web

Pour l'exécuter, il faut avoir le module `streamlit`
```bash
pip install streamlit
```

Puis exécuter via : 
```bash
streamlit run "Partie_1_LLM/interface.py"
```