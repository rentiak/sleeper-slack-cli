import sleeper_api
import slack_helper

def build_formatted_matchups_blocks(league_id, week):
  league_name = sleeper_api.league_api_call(league_id, "")["name"]
  rosters = sleeper_api.get_team_rosters(league_id)
  matchups = sleeper_api.get_matchups(league_id, week)
  standings = sleeper_api.get_standings(rosters)

  formatted_matchups = {"text" : f'{league_name} - Week {week} Matchups', "blocks":[slack_helper.slack_header_block(f'{league_name} - Week {week} Matchups')]}
  for matchup_id in sorted(matchups.keys()):
    full_matchup = matchups[matchup_id]
    team_1_name   = rosters[full_matchup["team_1"]["roster_id"]]["team_name"]
    team_1_place  = standings[rosters[full_matchup["team_1"]["roster_id"]]["team_name"]]["place"]
    team_1_wins   = rosters[full_matchup["team_1"]["roster_id"]]["settings"]["wins"]
    team_1_losses = rosters[full_matchup["team_1"]["roster_id"]]["settings"]["losses"]
    team_2_name   = rosters[full_matchup["team_2"]["roster_id"]]["team_name"]
    team_2_place  = standings[rosters[full_matchup["team_2"]["roster_id"]]["team_name"]]["place"]
    team_2_wins   = rosters[full_matchup["team_2"]["roster_id"]]["settings"]["wins"]
    team_2_losses = rosters[full_matchup["team_2"]["roster_id"]]["settings"]["losses"]
    formatted_matchups["blocks"].append(slack_helper.slack_text_block(f"*{team_1_place} - {team_1_name}* ({team_1_wins}-{team_1_losses}) vs *{team_2_place} - {team_2_name}* ({team_2_wins}-{team_2_losses})"))
    formatted_matchups["blocks"].append({"type": "divider"})

  return formatted_matchups

def build_formatted_results_blocks(league_id, week):
  league_name = sleeper_api.league_api_call(league_id, "")["name"]
  rosters = sleeper_api.get_team_rosters(league_id)
  matchups = sleeper_api.get_matchups(league_id, week)

  formatted_matchups = {"text" : f'{league_name} - Week {week} Results', "blocks":[slack_helper.slack_header_block(f'{league_name} - Week {week} Results')]}
  for matchup_id in sorted(matchups.keys()):
    full_matchup = matchups[matchup_id]
    team_1_name   = rosters[full_matchup["team_1"]["roster_id"]]["team_name"]
    team_1_score  = full_matchup["team_1"]["points"]
    team_2_name   = rosters[full_matchup["team_2"]["roster_id"]]["team_name"]
    team_2_score  = full_matchup["team_2"]["points"]
    if team_1_score > team_2_score:
      team_1_emoji = ":trophy:"
      team_2_emoji = ":sad-panda:"
    elif team_2_score > team_1_score:
      team_1_emoji = ":sad-panda:"
      team_2_emoji = ":trophy:"
    else:
      team_1_emoji, team_2_emoji = "::neutral_face::"
    formatted_matchups["blocks"].append(slack_helper.slack_text_block(f"{team_1_emoji} *{team_1_name}* ({team_1_score}) vs *{team_2_name}* ({team_2_score}) {team_2_emoji}"))
    formatted_matchups["blocks"].append({"type": "divider"})

  return formatted_matchups

def build_formatted_standings_blocks(league_id):
  league_name = sleeper_api.league_api_call(league_id, "")["name"]
  rosters = sleeper_api.get_team_rosters(league_id)
  standings = sleeper_api.get_standings(rosters)

  formatted_standings = {"text" : f'{league_name} Standings', "blocks":[slack_helper.slack_header_block(f'{league_name} Standings')]}
  place = 1
  for team_name in standings:
    formatted_standings["blocks"].append(slack_helper.slack_text_block(f"*{place} {team_name}* ({standings[team_name]['wins']}-{standings[team_name]['losses']}-{standings[team_name]['fpts']}pts)"))
    place += 1

  return formatted_standings

def build_formatted_outliers_blocks(league_id, week):
  league_name = sleeper_api.league_api_call(league_id, "")["name"]
  rosters = sleeper_api.get_team_rosters(league_id)
  outliers = sleeper_api.get_outliers(league_id, week)

  boom_player = outliers["boom_player"]
  bust_player = outliers["bust_player"]
  negatives   = outliers["negatives"]
  started_out = outliers["started_out"]

  formatted_outliers = {"text" : f'{league_name} Outliers', "blocks":[]}
  formatted_outliers["blocks"].append(slack_helper.slack_text_block(f':chart_with_upwards_trend: *Powerhouse*: {sleeper_api.get_all_players()[boom_player["player"]]["first_name"]} {sleeper_api.get_all_players()[boom_player["player"]]["last_name"]} ({rosters[boom_player["roster_id"]]["team_name"]})\nProjected: {boom_player["projected_score"]} Actual: {boom_player["actual_score"]}'))
  formatted_outliers["blocks"].append(slack_helper.slack_text_block(f':chart_with_downwards_trend: *Slacker*: {sleeper_api.get_all_players()[bust_player["player"]]["first_name"]} {sleeper_api.get_all_players()[bust_player["player"]]["last_name"]} ({rosters[bust_player["roster_id"]]["team_name"]})\nProjected: {bust_player["projected_score"]} Actual: {bust_player["actual_score"]}'))
  if negatives:
    formatted_outliers["blocks"].append(slack_helper.slack_text_block(":yikes: *Negative Points*:"))
    for negative in negatives:
      formatted_outliers["blocks"].append(slack_helper.slack_text_block(f'{sleeper_api.get_all_players()[negative["player"]]["first_name"]} {sleeper_api.get_all_players()[negative["player"]]["last_name"]} ({rosters[negative["roster_id"]]["team_name"]})\nProjected: {negative["projected_score"]} Actual: {negative["actual_score"]}\n'))
  if started_out:
    formatted_outliers["blocks"].append(slack_helper.slack_text_block(":confused_dog_head:  *Players Started Out*:"))
    for player in started_out:
      formatted_outliers["blocks"].append(slack_helper.slack_text_block(f'{sleeper_api.get_all_players()[player["player"]]["first_name"]} {sleeper_api.get_all_players()[player["player"]]["last_name"]} ({rosters[player["roster_id"]]["team_name"]})'))

  return formatted_outliers