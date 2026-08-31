# Mise en place — tableau de bord Championnats

Ce dépôt est un petit robot **gratuit et indépendant** de l'appli Loto Foot 7.
Son seul rôle : lire, quatre fois par jour, les pages publiques de résultats
et de calendrier de [betexplorer.com](https://www.betexplorer.com/) pour les
19 championnats suivis, et publier un résumé dans
`data/championnats.json`, que l'onglet **⚽ Championnats** de l'appli va
lire.

Pas de compte à créer, pas de clé à obtenir : ce robot lit simplement des
pages publiques comme le ferait un navigateur. Ça va plus vite qu'avec
API-Football, mais la contrepartie est expliquée en bas de page (« Ce que
fait — et ne fait pas — ce robot »).

Il faut environ 5 minutes, une seule fois.

## 1. Créer le dépôt GitHub

1. Sur https://github.com, clique sur « New repository ».
2. Nom au choix (par exemple `foot-dashboard-data`). **Le dépôt doit rester
   public** — un dépôt privé empêcherait l'appli de lire le fichier JSON
   depuis le navigateur (ça demanderait une authentification qu'une appli
   statique ne gère pas).
3. Ne coche aucune case d'initialisation (pas de README, pas de
   `.gitignore`) — le dépôt doit être vide.
4. Ajoute-y le contenu de ce dossier (`leagues.json`, `fetch.py`,
   `requirements.txt`, `.github/workflows/refresh.yml`,
   `data/championnats.json`) — via « Add file → Upload files » dans
   l'interface GitHub, ou en ligne de commande :

   ```
   git init
   git remote add origin https://github.com/<toi>/<ton-depot>.git
   git add .
   git commit -m "Robot championnats"
   git branch -M main
   git push -u origin main
   ```

   **Attention si tu glisses-déposes les fichiers un par un** : le dossier
   `.github/workflows/` doit impérativement conserver ce chemin exact —
   GitHub ne reconnaît un workflow que placé à `.github/workflows/*.yml`.
   Si tu n'es pas sûr que le glisser-déposer a bien gardé la structure de
   dossiers, la façon la plus fiable est de créer le fichier directement
   sur GitHub : « Add file → Create new file » puis taper
   `.github/workflows/refresh.yml` dans le champ du nom (les `/` créent
   les dossiers automatiquement), et coller le contenu du fichier.

## 2. Vérifier que les Actions sont actives

Onglet **Actions** de ton dépôt. Si un message propose de les activer,
clique dessus.

## 3. Lancer un premier rafraîchissement manuel

1. Onglet **Actions** → clique sur le workflow **« Rafraîchir les
   championnats »** dans la colonne de gauche.
2. En haut à droite de cette page, bouton **« Run workflow »** → confirme
   dans le petit panneau qui s'ouvre.
3. Attends 1-2 minutes, rafraîchis la page : un run vert ✅ doit
   apparaître.

Si le run échoue (❌), clique dessus pour voir les logs.

### Si un championnat reste sur « Aucune journée détectée »

C'est la contrepartie de ne pas utiliser d'API officielle : les adresses
des pages de résultats sur betexplorer.com peuvent changer si un
championnat est renommé ou restructuré d'une saison à l'autre — ça arrive
souvent en Amérique du Sud (l'Argentine en particulier change régulièrement
le nom de son tournoi selon le sponsor du moment).

Pour corriger :
1. Va sur https://www.betexplorer.com/football/<pays>/ (ex.
   `.../football/argentina/`) pour voir la liste actuelle des compétitions
   du pays.
2. Repère le championnat qui correspond, et note son adresse — le
   `slug` est ce qui suit `.../football/` dans l'URL de sa page de
   résultats (ex. pour `betexplorer.com/football/argentina/liga-profesional/results/`,
   le slug est `argentina/liga-profesional`).
3. Corrige le champ `"slug"` correspondant dans `leagues.json`, commit,
   relance le workflow.

## 4. Récupérer l'URL du fichier JSON et la coller dans l'appli

Une fois qu'un run a réussi, l'URL « brute » (raw) du fichier généré est :

```
https://raw.githubusercontent.com/<toi>/<ton-depot>/main/data/championnats.json
```

(remplace `<toi>` par ton nom d'utilisateur GitHub et `<ton-depot>` par le
nom du dépôt — et `main` par `master` si ton dépôt utilise encore cet
ancien nom de branche par défaut).

Dans l'appli Loto Foot 7 : onglet **⚽ Championnats** → colle cette URL dans
le champ « URL des données (JSON) » → « 💾 Enregistrer l'URL ». Les
championnats doivent s'afficher, groupés Europe / Amérique du Sud.

C'est terminé : le robot tourne désormais tout seul 4 fois par jour, entre
13h et minuit (heure de Paris), et l'appli se rafraîchit à chaque ouverture
de l'onglet (bouton « 🔄 Rafraîchir » pour forcer une relecture immédiate du
JSON déjà publié).

## Ce que fait — et ne fait pas — ce robot

- **Pas de clé, pas de compte, pas de quota** : contrairement à une API
  payante, il n'y a rien à souscrire ni à surveiller côté requêtes/jour.
- **En contrepartie, c'est plus fragile qu'une API officielle** : ce
  robot lit la mise en page actuelle de betexplorer.com. Si ce site change
  significativement sa mise en page, la lecture peut casser pour tout ou
  partie des championnats — ce n'est pas garanti dans la durée comme le
  serait un contrat d'API. Si ça arrive un jour, dis-le et on ajustera le
  code de lecture.
- Le robot fait des requêtes à un rythme volontairement mesuré (une pause
  entre chaque page, 4 passages/jour) — jamais de rafale de requêtes.
- Il ne fait **aucune notification ni alerte** : c'est un tableau de bord
  consulté à la demande, pas un système d'alerte temps réel.
- Il ne stocke aucune donnée personnelle — seulement les scores publics des
  championnats suivis.
- Les horaires du cron GitHub Actions sont en UTC et ne s'ajustent pas
  automatiquement à l'heure d'été/hiver française — un décalage d'environ
  1h est donc normal une partie de l'année, sans conséquence pour un
  tableau de bord consulté à la demande.
