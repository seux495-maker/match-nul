name: Rafraîchir les championnats

# 4 passages/jour, choisis pour tomber dans la fenêtre 13h-00h heure de
# Paris (celle où se jouent la majorité des matchs des championnats
# suivis). Pas de quota à gérer ici (contrairement à une API payante) —
# ce script lit simplement des pages publiques de betexplorer.com, avec
# une pause polie entre chaque requête (voir fetch.py). Cron GitHub
# Actions fonctionne en UTC sans ajustement heure d'été/hiver : les
# horaires ci-dessous visent 13h/16h30/20h/23h à Paris en hiver et
# dérivent d'environ 1h en été (14h/17h30/21h/00h) — acceptable pour un
# tableau de bord consulté à la demande, pas une alerte temps réel.
on:
  schedule:
    - cron: "0 12 * * *"
    - cron: "30 15 * * *"
    - cron: "0 19 * * *"
    - cron: "0 22 * * *"
  workflow_dispatch: {} # permet de déclencher un rafraîchissement manuel depuis l'onglet Actions de GitHub, pour tester sans attendre le prochain horaire
  push: # déclenche aussi un run frais à chaque commit sur main (ex. modifier
    branches: [main] # leagues.json ou README.md) — pratique sur mobile, pas besoin
    paths-ignore: # de trouver le bouton "Run workflow". paths-ignore évite que
      - "data/championnats.json" # le commit automatique du robot lui-même ne se redéclenche en boucle.

permissions:
  contents: write

concurrency:
  group: refresh-championnats
  cancel-in-progress: false

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Installer les dépendances
        run: pip install -r requirements.txt

      - name: Récupérer les résultats (betexplorer.com)
        run: python fetch.py

      - name: Publier si quelque chose a changé
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/championnats.json leagues.json
          if git diff --staged --quiet; then
            echo "Rien de nouveau, pas de commit."
          else
            git commit -m "Rafraîchissement automatique des championnats"
            git push
          fi
