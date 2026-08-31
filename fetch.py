#!/usr/bin/env python3
"""
Rafraîchit data/championnats.json à partir d'API-Football (api-sports.io)
pour la liste de championnats définie dans leagues.json.

Conçu pour rester sous le quota gratuit (100 requêtes/jour) même lancé
plusieurs fois par jour par le workflow GitHub Actions :

  - L'id API-Football de chaque championnat n'est résolu par recherche
    (nom + pays) qu'une seule fois, puis mis en cache dans leagues.json
    (champ "api_id") — plus jamais re-cherché ensuite.
  - La "journée en cours" (round) de chaque championnat n'est re-détectée
    qu'une fois par jour (champ "round_checked_on" comparé à la date du
    jour) — entre deux détections, on réutilise le round déjà connu pour
    aller chercher directement ses matchs (1 requête au lieu de 2).
  - Un budget dur (MAX_CALLS) arrête le script proprement avant d'épuiser
    le quota si jamais un jour a besoin d'exceptionnellement plus d'appels
    (ex. plusieurs championnats à re-détecter le même jour).

Résultat écrit dans data/championnats.json : { generated_at, leagues: [...] }
— c'est ce fichier que l'appli va lire (voir README de ce dépôt).
"""

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://v3.football.api-sports.io"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "leagues.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "championnats.json")
MAX_CALLS = 90  # marge de sécurité sous le quota gratuit de 100/jour (garde de la place pour des relances automatiques en cas d'erreur réseau/429)
FINISHED_STATUSES = {"FT", "AET", "PEN"}

calls_used = 0


def api_get(path, params, api_key):
    global calls_used
    qs = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{qs}"
    req = urllib.request.Request(url, headers={"x-apisports-key": api_key})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                calls_used += 1
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} sur {path} {params} : {e.read().decode(errors='replace')[:200]}", file=sys.stderr)
            if e.code == 429:
                time.sleep(2)
                continue
            return None
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  Erreur réseau sur {path} {params} : {e}", file=sys.stderr)
            time.sleep(2)
    return None


def current_season_guess():
    # API-Football identifie une saison par son année de DÉBUT (la saison
    # 2025 = 2025-2026 en Europe, où l'essentiel des championnats de cette
    # liste démarrent entre juin et août). On bascule sur la nouvelle année
    # de saison à partir de juillet.
    now = datetime.datetime.utcnow()
    return now.year if now.month >= 7 else now.year - 1


def resolve_league_id(name, country, api_key):
    data = api_get("/leagues", {"name": name, "country": country}, api_key)
    if not data:
        return None
    resp = data.get("response") or []
    if not resp:
        return None
    return resp[0]["league"]["id"]


def resolve_current_round(league_id, season, api_key):
    data = api_get("/fixtures/rounds", {"league": league_id, "season": season, "current": "true"}, api_key)
    if not data:
        return None
    resp = data.get("response") or []
    return resp[0] if resp else None


def fetch_round_fixtures(league_id, season, round_name, api_key):
    data = api_get("/fixtures", {"league": league_id, "season": season, "round": round_name}, api_key)
    if not data:
        return []
    return data.get("response") or []


def summarize(fixtures):
    total = len(fixtures)
    played = 0
    draws = 0
    for fx in fixtures:
        status = (fx.get("fixture") or {}).get("status", {}).get("short")
        if status in FINISHED_STATUSES:
            played += 1
            goals = fx.get("goals") or {}
            home, away = goals.get("home"), goals.get("away")
            if home is not None and away is not None and home == away:
                draws += 1
    return total, played, draws


def main():
    api_key = os.environ.get("API_FOOTBALL_KEY")
    if not api_key:
        print("Variable d'environnement API_FOOTBALL_KEY manquante.", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    today = datetime.date.today().isoformat()
    season = current_season_guess()
    results = []

    for league in config["leagues"]:
        if calls_used >= MAX_CALLS:
            print(f"Budget de requêtes atteint ({calls_used}) — arrêt avant « {league['name']} ».")
            break

        print(f"→ {league['name']} ({league['country']})")

        if not league.get("api_id"):
            league["api_id"] = resolve_league_id(league["name"], league["country"], api_key)
            if not league["api_id"]:
                print(f"  Introuvable côté API-Football : ajuste 'name'/'country' dans leagues.json.")
                continue

        need_round_refresh = league.get("round_checked_on") != today or not league.get("current_round")
        if need_round_refresh:
            round_info = resolve_current_round(league["api_id"], season, api_key)
            if round_info:
                league["current_round"] = round_info
                league["round_checked_on"] = today
            elif not league.get("current_round"):
                print("  Aucune journée en cours détectée (saison peut-être terminée ou pas encore commencée).")
                continue

        round_name = league.get("current_round")
        if not round_name:
            continue

        fixtures = fetch_round_fixtures(league["api_id"], season, round_name, api_key)
        total, played, draws = summarize(fixtures)
        print(f"  {round_name} : {played}/{total} joués, {draws} nul(s)")

        results.append(
            {
                "id": league["id"],
                "name": league["name"],
                "country": league["country"],
                "zone": league["zone"],
                "round": round_name,
                "matches_total": total,
                "matches_played": played,
                "draws": draws,
            }
        )

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "leagues": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")

    print(f"\nOK — {len(results)}/{len(config['leagues'])} championnats mis à jour, {calls_used} requête(s) API utilisée(s).")


if __name__ == "__main__":
    main()
