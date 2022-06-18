import json
import os
from datetime import date
import s3fs


fs = s3fs.S3FileSystem(anon=False)
fs.ls('email-entrapment-buck')
bucket = os.environ.get('S3_LOCATION') 

def send_message(event, say):
    with fs.open(bucket+'/users.json', 'r') as f:
        users = json.load(f)
    # emails sent to slackbot do not have a text attribute
    if event['text']=='':
        email = event["files"][0]

        # TODO: if f"CHECKED_{email['id']}" in os.environ or "X-Slack-Retry-Num" in request.headers:
        # This email has already been processed
            

        email_provider = "http://gmail.com/"

        sender_email = email["from"][0]["original"]
        email_subject = email["title"]
        email_content = "```" + email["plain_text"] + "```"
        timestamp = email["timestamp"]

        all_to = ', '.join([i["original"] for i in email["to"]])
        all_cc = ', '.join([i["original"] for i in email["cc"]])
            
        data = [
             {
                    "fallback": "An email was sent by " + sender_email,
                    "color": "#2196F3",
                    "pretext": "",
                    "author_name": sender_email,
                    "author_link": email_provider,
                    "author_icon": "",
                    "title": email_subject,
                    "title_link": email_provider,
                    "text": email_content,
                    "fields": [],
                    "footer": "Sent to : " + all_to,
                    "footer_icon": "",
                    "ts": timestamp
            }
            ]
        for i in users:
            if users[str(i)]['email'] == sender_email[sender_email.index("<")+1:-1]:
                users[str(i)]['has_posted'] = 1
                users[str(i)]['last_updated'] = str(date.today())
            else:
                print(users[str(i)]['email'])
                print(sender_email[sender_email.index("<")+1:-1])

        if all_cc:
            data[0]["fields"].append({
                "title": "cc",
                "value": all_cc
            })

        if email["attachments"]:
            data[0]["fields"].append({
                "title": "",
                "value": "This email also has attachments",
                "short": False
            }
            )
        print(data)
        print(users)
        with fs.open(bucket+'/users.json', 'w') as f:
            json.dump(users, f)
        say(
            channel=os.environ.get("SLACK_EMAILS_CHANNEL"),
            attachments=data,
            text='Email received from %s' % sender_email
            )
    else:
    # was not an email
        print(event)
        print("Successfully did not do anything")
        

def track_users(ack, say, command):
    with fs.open(bucket+'/users.json', 'r') as f:
        users = json.load(f)
    it = len(users)
    ack()
    user, email = command['text'].split(', ')
    users.update({str(it): {"Name": user, "email" : email, "has_posted" : 0, "last_updated" : str(date.today())} })
    print(users)
    with fs.open(bucket+'/users.json', 'w') as f:
        json.dump(users, f)
    say(f"Tracking {command['text']}. (WIP)")


def print_report(ack, say, command):
    with fs.open(bucket+'/users.json', 'r') as f:
        users = json.load(f)
    users['0']['last_updated'] = str(date.today())
    users['0']['Name'] = "Dummy user"
    users['0']['email'] = "email@example.com"
    users['0']['has_posted'] = 1
    ack()
    for i in users:
        if users[i]['last_updated'] != str(date.today()):
            users[i]['has_posted'] = 0
    with fs.open(bucket+'/users.json', 'w') as f:
        json.dump(users,f)
    has_posted = [users[str(iterator)]["Name"] for iterator in users if (users[str(iterator)]["has_posted"] == 0)]
    if len(has_posted) == 0:
        text = "Everyone has posted their status updates!"
    elif len(has_posted) == 1:
        text = has_posted[0] + " has not posted their status update."
    else:
        text = ', '.join(has_posted) + " have not posted their status updates."
    say(text)
    # say("Report is a work in Progress.")
