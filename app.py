import os
import logging
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
import slackbot_welcoming
import slackbot_emails
import slackbot_memes
import slackbot_ctf
import s3fs
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler

oauth_settings = OAuthSettings(
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECRET"),
)

app = App(

    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    # oauth_settings=oauth_settings
)

logging.basicConfig(level=logging.INFO)


# function that asks for intros
@app.event("team_join")
def handler(event, say):
    slackbot_welcoming.ask_for_introduction(event, say)


# triggered when messages are sent to Slackbot
@app.event("message")
def handler(event, say):
    slackbot_emails.send_message(event, say)


@app.command("/track")
def handler(ack, say, command):
    slackbot_emails.track_users(ack, say, command)

@app.command("/report")
def handler(ack, say, command):
    slackbot_emails.print_report(ack, say, command)


@app.command("/memes")
def handler(ack, say, command):
    slackbot_memes.post_memes(ack, say, command)

@app.command("/ctf")
def handler(client, ack, say, command):
    slackbot_ctf.ctf_func(client, ack, say, command)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
