import os

def ask_for_introduction(event, say):
    channel_id = os.environ.get("SLACK_INTRO_CHANNEL")
    user_id = event["user"]["id"]
    welcoming_string = f"Welcome to the team, <@{user_id}>! 🎉 Please give a short intro about yourself to the team.\nIn the intro, you can specfiy your interests, skills (can range from cooking to coding, doesn't matter!), hometown, mother tongue, branch etc.\nNothing formal, we are friends now! 😊\n"
    say(text=welcoming_string, channel=channel_id)
