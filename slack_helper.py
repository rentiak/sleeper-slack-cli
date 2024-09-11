import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def slack_header_block(text):
  return {
    "type": "header",
    "text": {
      "type": "plain_text",
      "text": text,
      "emoji": True
    }
  }

def slack_text_block(text):
  return {
    "type": "section",
    "text": {
      "type": "mrkdwn",
      "text": text
    }
  }

def send_slack_blocks(slack_token, slack_channel, content):
  client = WebClient(token=slack_token)
  try:
      response = client.chat_postMessage(
          username="onX Sleeper FF Bot",
          icon_url="https://sleepercdn.com/images/v2/icons/league/nfl/purple.png",
          channel=slack_channel,
          text=content["text"], # Slack best practice to have a message summary for use in mobile notifications
          blocks=json.dumps(content["blocks"])
      )
  except SlackApiError as e:
      # You will get a SlackApiError if "ok" is False
      assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'