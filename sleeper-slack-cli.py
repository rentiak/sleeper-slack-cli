# cSpell:disable

import argparse
import os
import slack_helper
import sleeper_api
import message_formatting

if __name__ == "__main__":
  description = "This CLI queries sleeper for a particular league and then sends various Slack messages based on the type specified."

  parser = argparse.ArgumentParser(description=description)
  parser.add_argument("message_type", choices=["matchups", "standings", "results"])
  args = parser.parse_args()

  # Get configuration from ENV
  slack_channel = os.environ["SLACK_CHANNEL"]
  slack_token = os.environ["SLACK_TOKEN"]
  leagues =  os.environ["SLEEPER_LEAGUES"].split()

  # The week to use isn't as simple as it seems
  nfl_state = sleeper_api.api_call("state/nfl")
  matchup_week = nfl_state["week"]         # The 'actual' week looking forward
  results_week = nfl_state["display_week"] # Sending after the week ends, but before the UI 'moves on'

  # Run that beautiful Fantasy footage
  match args.message_type:
    case "matchups":
      for league_id in leagues:
        slack_helper.send_slack_blocks(slack_token, slack_channel, message_formatting.build_formatted_matchups_blocks(league_id, matchup_week))
    case "standings":
      for league_id in leagues:
      
        slack_helper.send_slack_blocks(slack_token, slack_channel, message_formatting.build_formatted_standings_blocks(league_id))
    case "results":
      for league_id in leagues:
        # Generate blocks first so the messages get sent essentially simultaneously rather than a delay in stat processing
        results_blocks = message_formatting.build_formatted_results_blocks(league_id, results_week)
        outliers_blocks = message_formatting.build_formatted_outliers_blocks(league_id, results_week)
        slack_helper.send_slack_blocks(slack_token, slack_channel, results_blocks)
        slack_helper.send_slack_blocks(slack_token, slack_channel, outliers_blocks)
