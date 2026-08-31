# foot-dashboard-data

Robot gratuit et indépendant qui alimente l'onglet **⚽ Championnats** de
l'appli Loto Foot 7. Il lit quatre fois par jour (13h/16h30/20h/23h, heure
de Paris) les pages publiques de [betexplorer.com](https://www.betexplorer.com/)
via un workflow GitHub Actions planifié, et publie le résultat dans
[`data/championnats.json`](data/championnats.json) : pour chacun des 19
championnats suivis, la journée en cours, le nombre de matchs joués sur le
total, et le nombre de matchs nuls.

Pas de clé d'API, pas de compte à créer : `fetch.py` lit simplement des
pages publiques, comme le ferait un navigateur.

**➡️ Pour tout mettre en place (dépôt GitHub, premier lancement, URL à
coller dans l'appli), suis [SETUP.md](SETUP.md).**

## Contenu du dépôt

- `leagues.json` — la liste des 19 championnats suivis (id, nom, pays,
  zone, et l'adresse de sa page sur betexplorer.com).
- `fetch.py` — le script qui lit betexplorer.com et écrit
  `data/championnats.json` (voir les commentaires en tête du fichier pour
  le détail de la logique de détection de la journée en cours).
- `requirements.txt` — dépendance Python nécessaire (`beautifulsoup4`,
  pour lire les pages).
- `.github/workflows/refresh.yml` — le workflow planifié qui exécute
  `fetch.py` 4 fois par jour et republie `data/championnats.json`.
- `data/championnats.json` — le fichier lu par l'appli (placeholder vide
  tant que le workflow n'a pas encore tourné une première fois).

## Limite à connaître

Ce robot lit la mise en page publique de betexplorer.com plutôt qu'une API
officielle — c'est ce qui permet de rester 100% gratuit sans compte ni
quota, mais ça le rend aussi plus sensible aux changements de mise en page
du site, et certains championnats (surtout en Amérique du Sud, où les noms
de tournois changent selon les saisons/sponsors) peuvent occasionnellement
nécessiter une petite correction dans `leagues.json` — voir la section
correspondante de SETUP.md.
