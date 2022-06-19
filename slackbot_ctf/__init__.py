import json
import os
import re
import requests
from datetime import timezone, datetime, timedelta
import pytz
import s3fs
import feedparser
import ctfd
import shutil
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file']

# headers = {"accept-encoding": "gzip, deflate, br", "accept-language": "en-US,en;q=0.9", "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36"}
# moooom, ctftime has blocked me yet again for using a cli
headers = { "authority": "ctftime.org",
           "pragma": "no-cache",
           "cache-control": "no-cache",
           "sec-ch-ua-mobile": "?0",
           "upgrade-insecure-requests": "1",
           "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
           "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
           "sec-fetch-site": "none",
           "sec-fetch-mode": "navigate",
           "sec-fetch-user": "?1",
           "sec-fetch-dest": "document",
           "accept-language": "en-US,en;q=0.9"
           }


bucket = os.environ.get("S3_LOCATION")
fs = s3fs.S3FileSystem(anon=False)

def logger(client, ack, say, command, users):
    print(users)
    client.chat_postMessage(
        channel = command['channel_id'],
        icon_url=users[command['user_id']],
        username=command['user_name'],
        text=f"/ctf {command['text']}"
    )


def ctf_func(client, ack, say, command):
    try:
        with open('slack_users.json', 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = client.users_list()
        usersbutBetter = {users['members'][i]['id']:users['members'][i]['profile']['image_72'] for i in range(len(users['members']))}
        with open('slack_users.json', 'w') as f:
            json.dump(usersbutBetter, f)
    # call different functions based on the slash command used
    if command['text'] == "help":
        ctf_help(client, ack, say, command, users)
    elif command['text'][:4] == "add ":
        ctf_add(client, ack, say, command, users)
    elif command['text'][:9] == "upcoming ":
        ctf_upcoming(client, ack, say, command, users)
    elif command['text'][:9] == "addcreds ":
        ctf_addcreds(client, ack, say, command, users)
    elif command['text'][:10] == "showcreds ":
        ctf_showcreds(client, ack, say, command, users)
    elif command['text'][:7] == "archive":
        ctf_archive(client, ack, say, command, users)
    elif command['text'][:5] == "check":
        ctf_check(client, ack, say, command, users)
    elif command['text'][:3] == "sub":
        ctf_subscribe(client, ack, say, command, users)
    else:
        ack()
        print(command['text'])
        say("Invalid command")


def ctf_help(client, ack, say, command, users):
    ack()
    help_text = """
This is the help text for the /ctf slash command. Available functions are:
/ctf help := Displays this block of text
/ctf add <ctftime url>  := adds the url to the list of CTFs to participate in. Sets a slack reminder for a CTF based on the time given on CTFTime.
/ctf upcoming enddate (only dd-mm-yyyy or dd/mm/yyyy) := Gives a list of CTFs, their scores and starting dates for the timeframe of startdate-enddate
/ctf addcreds CTF:<ctftime url>, username:XXXX, password:YYYY := Store CTF credentials, and make it accessible using /ctf showcreds
/ctf showcreds <search param> := Returns an action to choose CTF from stored ones
/ctf archive := Logs in with creds given from addcreds, gets challs and description, and stores them off on S3
/ctf check := check for new CTFs within a week and add them.
    """
    #logger(ack, say, command)
    client.chat_postEphemeral(text=help_text, channel=command['channel_id'], user=command['user_id'])


def ctf_add(client, ack, say, command, users):
    ack()
    # get url
    url = command['text'][4:].strip()
    regex_text = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    # confirm that previous "url" was in fact a url
    url = re.findall(regex_text, url)[0]
    # get event ID
    event_id = url.split('/')[4]
    request_url = "https://ctftime.org/api/v1/events/"+event_id+"/"
    # why are headers even required? hell
    global headers

    # fetch details from CTFTime API
    r = requests.get(request_url, headers=headers)

    start = r.json()['start']
    end = r.json()['finish']
    title = r.json()['title']
    ddate = [int(i) for i in re.split('-|:|T', start)[:5]]

    # this is the date of the CTF, in UTC
    # replace UTC time with IST time

    date = datetime(ddate[0], ddate[1], ddate[2], ddate[3], ddate[4], 00) - timedelta(minutes=30)
    text = f"<@{command['user_id']}> has added {title}, starts at {start[:start.index('T')]} ({start[start.index('T')+1:start.index('+')]} UTC) and ends at {end[:end.index('T')]} ({end[end.index('T')+1:end.index('+')]} UTC)"

    # use Slack Web API to add reminder

    client.reminders_add(
        token=os.environ.get("SLACK_USERTOKEN"),
        text=f"{title}, starts at {start[:start.index('T')]} ({start[start.index('T')+1:start.index('+')]} UTC)",
        time=int(date.timestamp())
    )

    client.chat_scheduleMessage(
        channel=command["channel_id"],
        post_at=int(date.timestamp()),
        text=f"@<!channel>, looks like we're participating in {title}!"
    )
    # logger(ack, say, command)
    say(text)


def ctf_upcoming(client, ack, say, command, users):
    global headers
    # get end dates
    args = re.split('[-/]', command['text'][8:].strip())
    if len(args) == 3:
        # it's a date!
        request_date = int(datetime(int(args[2]), int(args[1]), int(args[0])).replace(tzinfo=timezone.utc).timestamp())
        timestamp_now = int(datetime.now().timestamp())
        request_url = "https://ctftime.org/api/v1/events/?limit=5&"+"start="+str(timestamp_now)+"&finish="+str(request_date)
        print(request_url)
        r = requests.get(request_url, headers=headers).json()
        text = ""
        for i in range(len(r)):
            text += f"CTF Name : {r[i]['title']}\n"
            text += f"CTF URL : {r[i]['ctftime_url']}\n"
            text += f"CTF Points: {r[i]['weight']}\n"
        if text == "":
            text = "No CTFs in this timeframe"
    else:
        text = ' '.join(args)
    ack()
    logger(client, ack, say, command, users)
    say(text)


def ctf_addcreds(client, ack, say, command, users):
    ack()
    try:
        with fs.open(bucket+"/credentials.json", 'r') as f:
            creds = json.load(f)
    except:
        # json file does not exist
        creds = {}
        with fs.open(bucket+"/credentials.json", 'w') as f:
            json.dump(creds, f)
    text = command['text'][8:].strip().split(',')
    print(text)
    username = text[1].replace("username:", "").strip()
    password = text[2].replace("password:", "").strip()
    url = text[0].replace("CTF:", "").strip()
    regex_text = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    # confirm that previous "url" was in fact a url
    url = re.findall(regex_text, url)[0]
    # get event ID
    event_id = url.split('/')[-1]
    request_url = "https://ctftime.org/api/v1/events/"+event_id+"/"
    global headers

    # fetch details from CTFTime API
    r = requests.get(request_url, headers=headers)
    print(r)
    r = r.json()
    creds.update({str(len(creds)): {"CTF": r['title'], "Username": username, "Password": password, "URL": r['url']}})
    with fs.open(bucket+"/credentials.json", "w") as f:
        json.dump(creds, f)
    logger(client, ack, say, command, users)
    try: 
        ctfd.main(username, password, url)
    except Exception as e:
        say(f"Exception raised: {e}")
    #say(f'Added {username}, {password}, under {r["title"]}')
    os.chdir('../../')
    print(os.listdir('.'))
    shutil.make_archive(r["title"],'zip',"CTF/")
    #flow = InstalledAppFlow.from_client_secrets_file('credentials_from_google_app.json', ['https://www.googleapis.com/auth/drive.metadata.readonly','https://www.googleapis.com/auth/drive.file'])
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': 'CTFd.zip', 'parents': [os.environ.get("DRIVE_ID")]}
    media = MediaFileUpload('CTFd.zip', mimetype='application/zip')
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()

    say(f'Added {username}, {password}, under {r["title"]}')


def ctf_showcreds(client, ack, say, command, users):
    ack()
    with fs.open(bucket+"/credentials.json", "r") as f:
        creds = json.load(f)
    check = command['text'][9:].strip().lower()
    text = f"These are the matches for {check}:\n"
    for i in range(len(creds)):
        if check in creds[str(i)]["CTF"].lower():
            text += f'CTF Name: {creds[str(i)]["CTF"]}\n'
            text += f'CTF URL: {creds[str(i)]["URL"]}\n'
            text += f'Username: {creds[str(i)]["Username"]}\n'
            text += f'Password: {creds[str(i)]["Password"]}\n'
    logger(client, ack, say, command, users)
    say(text)


def ctf_archive(client, ack, say, command, users):
    ack()
    logger(client, ack, say, command, users)
    say("Deprecated! Use addcreds")


def ctf_check(client, ack, say, command, users):
    ack()
    logger(client, ack, say, command, users)
    request_date = int((datetime.now() + timedelta(days=7)).timestamp())
    timestamp_now = int(datetime.now().timestamp())
    request_url = "https://ctftime.org/api/v1/events/?limit=1000&"+"start="+str(timestamp_now)+"&finish="+str(request_date)
    print(request_url)
    r = requests.get(request_url, headers=headers).json()
    for i in range(len(r)):
        if r[i]['weight'] > 0:
            command['text'] = f"add {r[i]['ctftime_url'][:-1]}"
            ctf_add(client, ack, say, command, users)

def ctf_subscribe(client, ack, say, command, users):
    ack()
    logger(client, ack, say, command, users)
    try:
        with open("subscriptions.json",'r') as f:
            subs = json.load(f)
    except FileNotFoundError:
        subs = {i: [] for i in users.keys()}
        with open("subscriptions.json", 'w') as f:
            json.dump(subs, f)
    print(command)
    subs[command['user_id']].append(command['text'][4:])
    with open("subscriptions.json", 'w') as f:
        json.dump(subs,f)

