 WIP Slackbot for c0d3_h4cki05.
 
 Inspired by [OTA's Slackbot](https://github.com/OpenToAllCTF/OTA-Challenge-Bot), and uses code from [email-to-slack](https://github.com/kossiitkgp/email-to-slack) as well as [CTFdScraper](https://github.com/hanasuru/CTFdScraper).
 
# Features

- Uses the CTFTime API to automate a bunch of tasks like checking for information about new CTFs, and reminding users about them.
- Uses the Reddit (praw) API to randomly select a meme (default sub is [r/dankmemes](https://old.reddit.com/r/dankmemes)) and post it in a channel
- Uses code from email-to-slack to send emails to a specific channel in Slack.
- Uses code from [CTFdScraper](https://github.com/hanasuru/CTFdScraper) to scrape CTFd instances and upload to Google Drive.

# Installation
1. `python3 -m pip -r requirements.txt`
2. `python3 app.py`
Please make sure to, at the very least, define the shell variables `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` to make sure that the app at least starts up.
I use a bunch of environment vars to make my installation more portable to other teams.

Here's a list:

Essential Config Variables | Use
--------------- | ----
SLACK_BOT_TOKEN | Used by the slack-bolt framework as a bot token
SLACK_SIGNING_SECRET | Signing secret. Used to make sure that the bot is who it says it is.
APP_ID | One of the ways to figure out what app is talking to the program.
CLIENT_ID | Slack API Client ID, legacy way to figure out the client.
CLIENT_SECRET | Slack API Client Secret, again legacy.

AWS Config Variables | Use
-------------------- | -------
AWS_ACCESS_KEY_ID | AWS S3 Access Key. Used because I host on Heroku, without any persistent storage.
AWS_SECRET_ACCESS_KEY | AWS S3 Secret. 

Reddit Config Variables | Use
----------------------- | ------
REDDIT_CLIENT_ID | Used by praw. [Here's a guide to navigating this madness.](https://praw.readthedocs.io/en/latest/getting_started/configuration.html#configuration)
REDDIT_CLIENT_SECRET | Used by praw.
REDDIT_USERNAME | Self-explanatory.
REDDIT_PASSWORD | Self-explanatory.
REDDIT_USER_AGENT | Self-explanatory.

Misc Config Variables | Use
--------------------- | ------
SLACK_INTRO_CHANNEL | Posts a welcome message if someone joins the server, in this channel
SLACK_EMAILS_CHANNEL | Keeps the team updated and in check about the emails sent as status updates.
SLACK_MEMES_CHANNEL | Memes can only be posted in this channel.

# TODO
 
- [x] Use S3 storage bucket instead of ephemeral storage
- [x] Improve logging
- [] Use a more normal configuration system, like a json file
- [] Add more features and better README
