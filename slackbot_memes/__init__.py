import os
import praw
import random


def post_memes(client, ack, say, command):
    ack()
    reddit = praw.Reddit(client_id=os.environ.get("REDDIT_CLIENT_ID"),
                     client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                     user_agent=os.environ.get("REDDIT_USER_AGENT"),
                     username=os.environ.get("REDDIT_USERNAME"),
                     password=os.environ.get("REDDIT_PASSWORD"))
    try:
        sub = command["text"]
    except:
        sub = "dankmemes"
    if sub == "help":
        help_text = "This is the meme bot. Post any subreddit as the argument, say `/memes programmerhumor`, and it will get a random post from https://old.reddit.com/r/programmerhumor and post it here. Only allowed in #memes"
        client.chat_postEphemeral(text=help_text, channel=command['channel_id'], user=command['user_id']) 
    else:
        memes_submissions = reddit.subreddit(sub).hot()
        post_to_pick = random.randint(0,100)

        for i in range(0 ,post_to_pick):
            submission = next(x for x in memes_submissions if not x.stickied)
        user_id = command['user_id']
        if command['channel_id'] == os.environ.get("SLACK_MEMES_CHANNEL"):
            text = f"You asked for {sub}, <@{user_id}>, so here they are:\n" + submission.url
        else:
            text = f"You asked for {sub}, <@{user_id}>...\nhttps://i.kym-cdn.com/photos/images/newsfeed/001/671/387/17c.jpg"
        say(text)
