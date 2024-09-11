import requests

all_players = {}
week_stats = {}
projections = {}

def api_call(path):
  url=f"https://api.sleeper.app/v1/{path}"
  result = requests.get(url)
  return result.json()

def league_api_call(league_id, path):
  return api_call(f'league/{league_id}/{path}')

def get_all_players():
  global all_players # Only get players if we absolutely have to, it's low performance
  if not all_players:
    all_players = api_call("players/nfl")
  return all_players

def get_week_stats(week):
  global week_stats
  season_type = api_call("state/nfl")["season_type"]
  season = api_call("state/nfl")["season"]
  if not week_stats:
    week_stats = api_call(f"stats/nfl/{season_type}/{season}/{week}")
  return week_stats

def get_projections(week):
  global projections
  season = api_call("state/nfl")["season"]
  season_type = api_call("state/nfl")["season_type"]
  if not projections:
    projections = api_call(f"projections/nfl/{season_type}/{season}/{week}")
  return projections

def get_team_rosters(league_id):
  team_rosters = {}
  users = league_api_call(league_id, "users")
  rosters = league_api_call(league_id, "rosters")
  for roster in rosters:
    team_rosters[roster["roster_id"]] = roster
    user = [ user for user in users if roster["owner_id"] == user["user_id"] ][0]
    if "team_name" in user["metadata"]:
      team_name = user["metadata"]["team_name"]
    else:
      team_name = f'Team {user["display_name"]}'
    team_rosters[roster["roster_id"]]["user"] = user
    team_rosters[roster["roster_id"]]["team_name"] = team_name
  return team_rosters

def get_matchups(league_id, week):
  matchup_pairs = {}
  matchups = league_api_call(league_id, f"matchups/{week}")
  for matchup in matchups:
    if matchup["matchup_id"] not in matchup_pairs.keys():
      matchup_pairs[matchup["matchup_id"]] = { 'team_1' : matchup }
    else:
      matchup_pairs[matchup["matchup_id"]]['team_2'] = matchup
  return(matchup_pairs)

def calculate_player_score(league_id, player_stats):
  score = 0
  league_scoring_values = league_api_call(league_id, "")["scoring_settings"]
  for stat in player_stats:
    if stat in league_scoring_values: 
      score += player_stats[stat] * league_scoring_values[stat]
  return round(score,2)

def get_scored_roster(league_id, week_stats, roster):
  scored_roster = {
    "score" : 0, 
    "player_scores" : {},
    "did_not_play" : []
  }
  for player in roster["players"]:
    if player in week_stats:
      scored_roster["player_scores"][player] = calculate_player_score(league_id, week_stats[player])
      if player in roster["starters"]:
        scored_roster["score"] += scored_roster["player_scores"][player]
    else:
      scored_roster["player_scores"][player] = 0
      scored_roster["did_not_play"].append(player)
    return scored_roster

def get_standings(rosters):
  standings = []
  for roster in rosters:
    wins = rosters[roster]["settings"]["wins"]
    losses = rosters[roster]["settings"]["losses"]
    fpts = rosters[roster]["settings"]["fpts"]
    standings.append((wins, losses, fpts, roster))
    standings.sort(reverse = True)
  ordered_standings = {}
  for index, record in enumerate(standings):
    ordered_standings[rosters[record[3]]["team_name"]] = {
      "wins" : record[0],
      "losses" : record[1],
      "fpts" : record[2],
      "place" : index + 1
    }
  return ordered_standings

def simplify_matchup_results(league_id, matchups, week):
  week_stats = get_week_stats(week)
  projections = get_projections(week)
  simplified_rosters = {}
  for matchup_id, matchup in matchups.items():
    simplified_rosters[matchup["team_1"]["roster_id"]] = {
      "points"   : matchup["team_1"]["points"],
      "starters" : matchup["team_1"]['starters'],
      "players"  : {},
      "players_started_out" : [ starter for starter in matchup["team_1"]["starters"] if starter not in week_stats ]
    }
    for player in  matchup["team_1"]["players"]:
      simplified_rosters[matchup["team_1"]["roster_id"]]["players"][player] = {
        "score"           : matchup["team_1"]["players_points"][player],
        "projected_score" : calculate_player_score(league_id, projections[str(player)])
      }
    simplified_rosters[matchup["team_2"]["roster_id"]] = {
      "points"   : matchup["team_2"]["points"],
      "starters" : matchup["team_2"]['starters'],
      "players"  : {},
      "players_started_out" : [ starter for starter in matchup["team_2"]['starters'] if starter not in week_stats ]
    }
    for player in  matchup["team_2"]["players"]:
      simplified_rosters[matchup["team_2"]["roster_id"]]["players"][player] = {
        "score"           : matchup["team_2"]["players_points"][player],
        "projected_score" : calculate_player_score(league_id, projections[str(player)])
      }
  return simplified_rosters

def get_outliers(league_id, week):
  """
  Get some fun statistics to show off
  - Best player - biggest positive diff of actual and projected scores
  - Worst player - biggest negative diff of actual and projected scores
  - Negative players - players that had an actual score < 0
  - Started Out players - players on a starting roster that didn't actually play
  """
  matchups = get_matchups(league_id, week)
  simplified_matchup_results = simplify_matchup_results(league_id, matchups, week)
  boom_player = { "player" : "joeNobody", "roster_id" : 999999, "diff" : -999999 }
  bust_player = { "player" : "joeNobody", "roster_id" : 999999, "diff" : 999999 }
  negative_players = []
  started_out_players = []
  for roster, result in simplified_matchup_results.items():
    for player_id in result["starters"]:
      player = result["players"][player_id]
      score_diff =  (player["score"] - player["projected_score"])
      if score_diff > boom_player["diff"]:
        boom_player = { 
          "player" : player_id,
          "roster_id" : roster,
          "diff" : player["score"] - player["projected_score"],
          "projected_score" : player["projected_score"],
          "actual_score" : player["score"],
          }
      elif score_diff < bust_player["diff"]:
        bust_player = { 
          "player" : player_id,
          "roster_id" : roster,
          "diff" : player["score"] - player["projected_score"],
          "projected_score" : player["projected_score"],
          "actual_score" : player["score"],
          }
      if player["score"] < 0 :
        negative_players.append({ 
            "player" : player_id,
            "roster_id" : roster,
            "diff" : player["score"] - player["projected_score"],
            "projected_score" : player["projected_score"],
            "actual_score" : player["score"],
            })
      if player_id in result["players_started_out"]:
        started_out_players.append({ 
          "player" : player_id,
          "roster_id" : roster,
          })
  return {
    "boom_player" : boom_player,
    "bust_player" : bust_player,
    "negatives"   : negative_players,
    "started_out" : started_out_players
  }