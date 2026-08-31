# Mise en place — tableau de bord Championnats

Ce dépôt est un petit robot **gratuit et indépendant** de l'appli Loto Foot 7.
Son seul rôle : interroger l'API [API-Football](https://www.api-football.com/)
quatre fois par jour et publier un fichier `data/championnats.json` que
l'onglet **⚽ Championnats** de l'appli va lire. Aucune clé d'API ne transite
jamais par l'appli elle-même — elle ne fait que lire ce fichier JSON déjà
public.

Il faut environ 10 minutes, une seule fois.

## 1. Créer un compte API-Football gratuit

1. Va sur https://www.api-football.com/ et clique sur « S'inscrire » (ou
   directement https://dashboard.api-football.com/register).
2. Inscription gratuite, aucune carte bancaire demandée. Confirme ton
   e-mail si besoin.
3. Une fois connecté, va sur ton tableau de bord
   (https://dashboard.api-football.com/) : tu y trouveras ta clé API
   (« API-KEY »). Garde cette page ouverte, tu vas en avoir besoin à
   l'étape 3.
4. Le plan gratuit donne droit à **100 requêtes par jour** — largement
   suffisant ici, voir la section « Budget de requêtes » plus bas.

## 2. Créer le dépôt GitHub

1. Sur https://github.com, clique sur « New repository ».
2. Nom au choix (par exemple `foot-dashboard-data`). Peut être privé ou
   public, peu importe — le fichier JSON publié restera lisible via son URL
   « raw » quoi qu'il arrive tant que le dépôt est public ; **si tu choisis
   un dépôt privé, l'appli ne pourra pas lire le JSON depuis
   `raw.githubusercontent.com`** (ça demanderait une authentification que
   l'appli statique ne gère pas) — laisse-le donc **public**.
3. Ne coche aucune case d'initialisation (pas de README, pas de
   `.gitignore`) — le dépôt doit être vide.
4. Une fois le dépôt créé, ajoute-y le contenu de ce dossier
   (`leagues.json`, `fetch.py`, `.github/workflows/refresh.yml`,
   `data/championnats.json`) — soit en les glissant-déposant dans
   l'interface GitHub (« Add file » → « Upload files »), soit via `git` en
   ligne de commande si tu es à l'aise avec :

   ```
   git init
   git remote add origin https://github.com/<toi>/<ton-depot>.git
   git add .
   git commit -m "Robot championnats"
   git branch -M main
   git push -u origin main
   ```

## 3. Ajouter ta clé API comme secret GitHub

1. Dans ton dépôt GitHub, va dans **Settings → Secrets and variables →
   Actions**.
2. Clique sur « New repository secret ».
3. Nom : `API_FOOTBALL_KEY` (exactement, en majuscules).
4. Valeur : colle la clé API copiée à l'étape 1.
5. Valide.

Cette clé reste privée à GitHub Actions — elle n'apparaît jamais dans le
code, ni dans le fichier JSON publié, ni dans l'appli.

## 4. Vérifier que les Actions sont actives

Sur certains comptes, les GitHub Actions doivent être activées manuellement
pour un nouveau dépôt : va dans l'onglet **Actions** de ton dépôt. Si un
message propose de les activer, clique dessus.

## 5. Lancer un premier rafraîchissement manuel

Pas besoin d'attendre le prochain horaire programmé (13h/16h30/20h/23h,
heure de Paris) :

1. Onglet **Actions** → workflow « Rafraîchir les championnats » dans la
   liste à gauche.
2. Bouton « Run workflow » (en haut à droite) → « Run workflow ».
3. Attends 1-2 minutes, rafraîchis la page : un run vert ✅ doit apparaître.

Si le run échoue (❌), clique dessus pour voir les logs — la cause la plus
fréquente est une clé API absente ou mal collée (étape 3).

### Si un championnat reste introuvable

Dans les logs du run, un message du type :

```
Introuvable côté API-Football : ajuste 'name'/'country' dans leagues.json.
```

signifie que le nom/pays renseigné dans `leagues.json` ne correspond pas
exactement à ce qu'API-Football attend. Corrige la ligne concernée (ouvre
`leagues.json`, ajuste `name` et/ou `country`) puis relance le workflow
manuellement. Tu peux vérifier le nom exact attendu en cherchant le
championnat sur https://dashboard.api-football.com/soccer/ids (recherche
par pays).

## 6. Récupérer l'URL du fichier JSON et la coller dans l'appli

Une fois qu'un run a réussi, le fichier `data/championnats.json` est à jour
dans ton dépôt. Son URL « brute » (raw) est :

```
https://raw.githubusercontent.com/<toi>/<ton-depot>/main/data/championnats.json
```

(remplace `<toi>` par ton nom d'utilisateur GitHub et `<ton-depot>` par le
nom du dépôt — et `main` par `master` si ton dépôt utilise encore cet
ancien nom de branche par défaut).

Dans l'appli Loto Foot 7 : onglet **⚽ Championnats** → colle cette URL dans
le champ « URL des données (JSON) » → « 💾 Enregistrer l'URL ». Les
championnats doivent s'afficher immédiatement, groupés Europe / Amérique du
Sud.

C'est terminé : le robot tourne désormais tout seul 4 fois par jour, entre
13h et minuit (heure de Paris), et l'appli se rafraîchit à chaque ouverture
de l'onglet (bouton « 🔄 Rafraîchir » pour forcer une relecture immédiate du
JSON déjà publié, sans attendre le prochain passage du robot).

## Budget de requêtes (pourquoi 4 fois par jour, pas plus)

Le plan gratuit d'API-Football autorise 100 requêtes/jour. Avec 19
championnats suivis :

- Le tout premier passage de chaque journée doit à la fois détecter la
  journée en cours de chaque championnat *et* récupérer ses matchs
  (2 requêtes/championnat = 38 requêtes).
- Les passages suivants du même jour réutilisent la journée déjà détectée
  et ne font que rafraîchir ses matchs (1 requête/championnat = 19
  requêtes).

Donc 4 passages/jour = 38 + 19×3 = 95 requêtes au pire, sous la marge de
sécurité codée en dur dans `fetch.py` (`MAX_CALLS = 90`, pour garder de la
marge en cas de relance automatique après une erreur réseau passagère) —
et sous le quota réel de 100. Si tu modifies la liste des championnats
suivis ou la fréquence dans `.github/workflows/refresh.yml`, garde ce
calcul en tête pour ne pas dépasser le quota gratuit.

## Ce que fait — et ne fait pas — ce robot

- Il ne fait **aucune notification ni alerte** : c'est un tableau de bord
  consulté à la demande, pas un système d'alerte temps réel.
- Il ne stocke aucune donnée personnelle — seulement les scores publics des
  championnats suivis.
- Les horaires du cron GitHub Actions sont en UTC et ne s'ajustent pas
  automatiquement à l'heure d'été/hiver française (voir les commentaires
  dans `.github/workflows/refresh.yml`) — un décalage d'environ 1h est donc
  normal une partie de l'année, sans conséquence pour un tableau de bord
  consulté à la demande.
