#!/usr/bin/env python3
"""
Rafraîchit data/championnats.json en lisant les pages publiques de
betexplorer.com (résultats + calendrier) pour chaque championnat listé
dans leagues.json — pas de clé API, pas de compte, pas de quota.

Pour chaque championnat, on récupère deux pages :
  - .../results/   (matchs déjà joués, avec leur score)
  - .../fixtures/  (matchs à venir)
et on regroupe les matchs par journée ("N. Round" sur betexplorer) pour
identifier la journée la plus proche d'aujourd'hui, jouée ou en cours :

  - si la dernière journée apparue dans "results" est la même que la
    première journée apparue dans "fixtures" -> journée EN COURS
    (une partie jouée, une partie à venir) ; c'est le cas qui nous
    intéresse le plus.
  - sinon, on retombe sur la dernière journée connue côté résultats
    (journée terminée) ou, à défaut, la première à venir côté calendrier.

Ce script reste volontairement tolérant : une page absente, un format de
ligne inattendu, ou un championnat renommé/entre deux saisons ne fait pas
planter tout le run — juste ce championnat est ignoré ce jour-là (message
dans le journal), les autres continuent normalement.

Contrepartie du "pas de clé API, pas de compte" : ce script dépend de la
mise en page de betexplorer.com, qui peut changer sans préavis (à la
différence d'une API officielle). Si un jour beaucoup de championnats
d'un coup ne remontent plus rien, c'est le premier endroit à vérifier —
voir SETUP.md.
"""

import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "leagues.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "championnats.json")
BASE_URL = "https://www.betexplorer.com/football"

# Un User-Agent de navigateur courant : certains sites bloquent les
# requêtes qui n'en présentent aucun (signe évident de robot).
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

ROUND_RE = re.compile(r"^(\d+)\.\s*Round$", re.IGNORECASE)
SCORE_RE = re.compile(r"\[(\d+):(\d+)")

# Pause entre deux requêtes : on reste un visiteur poli, pas une rafale.
POLITE_DELAY = 1.2


def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} sur {url}", file=sys.stderr)
            if e.code in (429, 503):
                time.sleep(3)
                continue
            return None
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  Erreur réseau sur {url} : {e}", file=sys.stderr)
            time.sleep(3)
    return None


def parse_rounds(html):
    """Regroupe les lignes de match par journée, dans l'ordre d'apparition
    sur la page (betexplorer liste "results" du plus récent au plus ancien,
    et "fixtures" du plus proche au plus lointain — donc le premier numéro
    de journée rencontré est toujours le plus pertinent pour cette page).

    Retourne (rounds: {numéro: [ {played, home_goals, away_goals}, ... ]},
              order: [numéros de journée dans l'ordre d'apparition]).
    """
    soup = BeautifulSoup(html, "html.parser")
    rounds = {}
    order = []
    current_round = None

    for tr in soup.find_all("tr"):
        text = tr.get_text(" ", strip=True)
        if not text:
            continue

        m = ROUND_RE.match(text)
        if m:
            current_round = int(m.group(1))
            if current_round not in rounds:
                rounds[current_round] = []
                order.append(current_round)
            continue

        if current_round is None or " - " not in text:
            continue

        score_m = SCORE_RE.search(text)
        rounds[current_round].append(
            {
                "played": bool(score_m),
                "home_goals": int(score_m.group(1)) if score_m else None,
                "away_goals": int(score_m.group(2)) if score_m else None,
            }
        )

    return rounds, order


def analyze_league(slug):
    results_html = fetch_html(f"{BASE_URL}/{slug}/results/")
    time.sleep(POLITE_DELAY)
    fixtures_html = fetch_html(f"{BASE_URL}/{slug}/fixtures/")
    time.sleep(POLITE_DELAY)

    if not results_html and not fixtures_html:
        return None

    results_rounds, results_order = parse_rounds(results_html) if results_html else ({}, [])
    fixtures_rounds, fixtures_order = parse_rounds(fixtures_html) if fixtures_html else ({}, [])

    r_results = results_order[0] if results_order else None
    r_fixtures = fixtures_order[0] if fixtures_order else None

    if r_results is None and r_fixtures is None:
        return None

    if r_results is not None and r_results == r_fixtures:
        # Journée en cours : une partie déjà jouée (results), le reste à
        # venir (fixtures) — c'est le cas qui nous intéresse le plus.
        current = r_results
        played_rows = [m for m in results_rounds.get(current, []) if m["played"]]
        upcoming_rows = [m for m in fixtures_rounds.get(current, []) if not m["played"]]
        matches_played = len(played_rows)
        matches_total = matches_played + len(upcoming_rows)
    elif r_results is not None:
        # Dernière journée connue côté résultats, apparemment terminée
        # (rien de cette journée encore dans "fixtures").
        current = r_results
        played_rows = [m for m in results_rounds.get(current, []) if m["played"]]
        matches_played = len(played_rows)
        matches_total = matches_played
    else:
        # Rien encore joué : on retombe sur la prochaine journée à venir.
        current = r_fixtures
        matches_played = 0
        matches_total = len(fixtures_rounds.get(current, []))

    draws = sum(
        1
        for m in results_rounds.get(current, [])
        if m["played"] and m["home_goals"] == m["away_goals"]
    )

    return {
        "round": current,
        "matches_total": matches_total,
        "matches_played": matches_played,
        "draws": draws,
    }


def main():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    results = []

    for league in config["leagues"]:
        print(f"→ {league['name']} ({league['country']})")
        try:
            info = analyze_league(league["slug"])
        except Exception as e:  # on ne laisse jamais un championnat planter tout le run
            print(f"  Erreur inattendue : {e}", file=sys.stderr)
            info = None

        if not info:
            print(
                "  Aucune journée détectée (page introuvable, championnat entre deux "
                "saisons/renommé, ou format de page inattendu — voir SETUP.md)."
            )
            continue

        print(
            f"  Journée {info['round']} : {info['matches_played']}/{info['matches_total']} "
            f"joués, {info['draws']} nul(s)"
        )
        results.append(
            {
                "id": league["id"],
                "name": league["name"],
                "country": league["country"],
                "zone": league["zone"],
                "round": str(info["round"]),
                "matches_total": info["matches_total"],
                "matches_played": info["matches_played"],
                "draws": info["draws"],
            }
        )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "leagues": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")

    print(f"\nOK — {len(results)}/{len(config['leagues'])} championnats mis à jour.")


if __name__ == "__main__":
    main()
