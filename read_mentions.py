#!/usr/bin/env python3
import argparse

#https://www.tutorialgateway.org/python-strptime/
formats = [
    '%m/%d/%y %H%M',        #'12/31/18 2359'
    '%m/%d/%y %H:%M',       #'12/31/18 23:59'
    '%d/%m/%y %H:%M:%S',    #'31/12/18 23:59:58'
    '%d-%m-%Y %H:%M:%S',    #'10-12-2017 19:12:58' 
    '%d %B %Y %H:%M',       #'31 December 19 18:00'
    '%d %B %y %H:%M',       #'31 December 19 18:00'       
    '%d %B %Y',             #'31 December 2019'
    '%d %B %y',             #'31 December 19'
    '%d/%m/%y'              #'31/12/19'
]
# ==============================================================================
def provideFeedbackErroneousInvocation(error_msg,
                                        url, 
                                        headers,
                                        data,
                                        post_id,
                                        bot_id):
    """
    Downvote and reply to bad invocations, 
    along with help info for how to call this bot.
    """
    print(error_msg)
    post_url = f"{url}api/v4/posts"
    msg = "\nYou seem to be having trouble invoking my auto-tasker capability.\n"\
    "Invocation should start by @'ing this bot, followed by one task per line:\n"\
    "`|Taskname|DD/MM/YYYY HH:MM|required emoji|number (int) of estimated"\
    " minutes to complete. `\n**Note**: All suspenses MUST be within 3 weeks."\
    "\nPlease test in ~test_channel. You'll see a :jarvis: reaction around"\
    " the top of the hour when when your invocation is correct."\

    data['message'] = error_msg + msg

    resp = requests.post(post_url, headers=headers, data=json.dumps(data))
    if resp.status_code < 200 or resp.status_code > 299:
        pprint.pprint(json.loads(resp.text))
        print(f"Couldn't post response.  URL was '{post_url}'")
        print("Headers:")
        pprint.pprint(headers)
        sys.exit(-1)
    
    print("Reacting...")
    reaction_url = f"{url}api/v4/reactions"
    data = {}
    data['post_id'] = post_id
    data['user_id'] = bot_id
    data['emoji_name'] = "-1"
    resp = requests.post(reaction_url, 
                        headers=headers, 
                        data=json.dumps(data))
    if resp.status_code < 200 or resp.status_code > 299:
        pprint.pprint(json.loads(resp.text))
        print(f"Couldn't react via {reaction_url}'.  See the problem?")
        sys.exit(-1)
    else:
        print(resp.text)      
# ==============================================================================
def parse_task(post_id, message, channel_id, url, headers, bot_id):
    """
    Given a post, check for taskers in it, 
    extracting relevant info from the message body
    """
    tasks = []
    suspense = 0
    emojis = []
    task_id = 0
    #headers = {}
    headers.pop('per_page')
    headers.pop('include_deleted_channels')
    headers.pop('is_or_search')
    headers.pop('page')

    data = {}
    data['channel_id'] = channel_id
    data['root_id'] = post_id
    #https://www.geeksforgeeks.org/get-current-date-using-python/
    today = date.today()

    for line in message.split('\n'):
        if not line.startswith("|"):
            continue
        task = {}
        line = [x.strip() for x  in line.split("|")]
        task['task_id'] = line[1]

        if not re.fullmatch("[a-zA-Z0-9\-]{1,10}", task['task_id']):
            error_msg = f"Error: Something seems sketchy with the taskID:\n`{task['task_id']}`\n"
            error_msg += " Make sure it's alphanumeric (dashes okay) and < 10 chars"
            provideFeedbackErroneousInvocation(error_msg,
                                                url, 
                                                headers,
                                                data,
                                                post_id,
                                                bot_id)      
            continue


        for this_format in formats:
            try:
               task['suspense'] = datetime.strptime(line[2], this_format)
               task['task_id'] += datetime.strftime(task['suspense'], "%d%b%y")
               break
            except ValueError:
                pass
        if 'suspense' not in task:
            error_msg = f"Error: Bad date; try this format instead:\n`12/31/22 23:59`"
            provideFeedbackErroneousInvocation(error_msg,
                                                url, 
                                                headers,
                                                data,
                                                post_id,
                                                bot_id)
            continue

        emojis = [e for e in line[3].split() if ':' in e]
        task['emojis'] = emojis
       
        try:
            task['approx time burden (min)'] = int(line[4])
        except IndexError as e:
            task['approx. time burden (min)'] = 15

        if (task['suspense'] - datetime.now()).days >  22:
            error_msg = f"Error: Suspense is more than 3 weeks from now!"
            pprint.pprint(f"Suspense: {task['suspense']}" )
            print(error_msg)
            provideFeedbackErroneousInvocation(error_msg,
                                                url, 
                                                headers,
                                                data,
                                                post_id,
                                                bot_id)            
        else:
            task['suspense'] = datetime.strftime(task['suspense'], "%m/%d/%Y %H:%M")
            task['post_id'] = post_id
            tasks.append(task)
        
    if tasks:
        tasks = pd.DataFrame(tasks).dropna()
        print(f"Returning tasks of type{type(tasks)}:")
        pprint.pprint(tasks)     

        return tasks
    else:
        #print("Returning empty DF")
        return None
# ==============================================================================
def genCmd(args, task):
    """
    Generate the cmd to spawn the accountibility bot
    """
    print("genCMD")
    """
    Check the task ID for anything sketchy!
    1. Special characters (&, ;, etc)
    2. Non-printable characters
    3. ID longer than necessary (10+ characters)
    TODO: How to limit the NUMBER of children spawned to prevent a DOS?
    """    
    print(args)
    pprint.pprint(task)
    cmd = f"python3 accountability_mm_bot.py -a {args.authentication_info}"
    cmd += f" -c {args.channel}"
    if args.message_to_non_responders:
        cmd += f" -n {args.message_to_non_responders}"
    if args.message_to_responders:
        cmd += f" -m {args.message_to_responders}"
    if args.username_file:
        cmd += f" -u {args.username_file}"
    cmd += f" -d {task.suspense}"
    cmd += f" -i {task.task_id}"
    cmd += f" -l True"
    print(cmd)
    return task
# ==============================================================================
def main(args):      
    """
    Provided:
    1. Mattermost server URL,
    2. Team ID,
    3. Authentication token,
    4. bot name,  
    5. File of Mattermost usernames and/or channels 
    6. An emoji (or '*' for any emoji),
    Show which users from the list of usernames/channels provided have reacted 
    to the specified post with any emoji ('*'), or the specified emoji.
    Then, separately display all users who have NOT posted any emoji ('*'),
    or in the case of a specific emoji, 
    show those who have NOT reacted with that emoji.
    """                                              
    filter_on_usernames = False
    filter_on_channels = False
    results_per_page = 60 # Can up up to 200

    creds = parse_creds_from_file(args.authentication_info)
    url, team_id, token, bot_id = creds
    channels = []

    # Print current date + time for log review purposes
    print( str(datetime.now()).center(80, "=") )

    # Strip any quotes
    url = url.strip('"').strip("'")
    team_id = team_id.strip('"').strip("'")
    token = token.strip('"').strip("'")

    headers = { 
                "is_or_search": "true",
                "time_zone_offset": "0",
                "include_deleted_channels": "false",
                "page": "0",
                "per_page": str(results_per_page),
                "Authorization" : f"Bearer {token}"
            }
    # Get this team name
    team_url = f"{url}api/v4/teams/{team_id}"

    team_info = requests.get(team_url, headers=headers)
    if team_info.status_code == 200:
        team_info = json.loads(team_info.text)
        team_name = team_info["name"]

    else:
        print(f"Cannot find the team {team_id} on this server.")
        print(team_info)
        sys.exit(-1)

    # Get this bot info
    this_bot = get_bot_info(url, bot_id, headers)
    if not this_bot.empty:
        pprint.pprint(this_bot)
        bot_id = this_bot['user_id'].values[0]
    else:
        print(f"Could not find bot with ID {bot_id} on {url}")
        sys.exit(-1)         

    channel_url = url+f"api/v4/teams/{team_id}/channels/search"
    payload = {}
    payload["term"] = args.channel
    resp = requests.post(channel_url, headers=headers, data=json.dumps(payload))
    if resp.status_code >= 200 and resp.status_code < 400:
        channels = pd.DataFrame(json.loads(resp.text))
    else:
        print(f"Couldn't find channel {channel}")
        return

    if channels.empty:
        print("No matching channels")
        sys.exit(1)
    channels = channels[['id', 'name']]
    print("All matching channels:")
    pprint.pprint(channels)
    channel_id = channels['id'].values[0]


    users_url = url + "api/v4/users"
    all_users = get_users(users_url, headers, [], channels, results_per_page)
    pprint.pprint(all_users)

    search_url = f"{url}api/v4/teams/{team_id}/channels/search"
    payload["term"] = "update"

    results = search_keyword(args, url, headers, team_id, channels)
    #TODO Uncomment the 2 lines below to lock this down
    #user_id = all_users[all_users["username"]=="midnight"]["id"].values[0]
    #results = results[results["user_id"] == user_id]
    
    
    pprint.pprint(results.columns)
    pprint.pprint(results['message'])
    results = pd.DataFrame(results.to_dict('records'))
    tasks = pd.DataFrame()
    for row in results.itertuples():
        # Only parse task IF we haven't parsed it yet!
        reaction_url = f"{url}/api/v4/posts/{row.id}/reactions"
        resp = requests.get(reaction_url, headers=headers)
        if resp.status_code < 200 or resp.status_code > 299:
            pprint.pprint(json.loads(resp.text))
            print(f"URL was '{reaction_url}'.  See the problem?")
            sys.exit(-1)
        reactions = pd.DataFrame(json.loads(resp.text))

        if not reactions.empty and bot_id in reactions['user_id'].values:

            continue

        task = parse_task(row.id, 
                            row.message, 
                            channel_id, 
                            url, 
                            copy.deepcopy(headers),
                            bot_id)
        new_task = False
        try:
            if task and any(task):
                tasks = tasks.append(task)
                new_task = True
        except TypeError as e:
            print(f"TypeError: {e}")
        except ValueError as e:
            if any(task):
                tasks = tasks.append(task)
                new_task = True

        if new_task:
            print("Reacting...")
            reaction_url = f"{url}api/v4/reactions"
            data = {}
            data['post_id'] = row.id
            data['user_id'] = bot_id
            data['emoji_name'] = "jarvis"
            resp = requests.post(reaction_url, 
                                headers=headers, 
                                data=json.dumps(data))
            if resp.status_code < 200 or resp.status_code > 299:
                pprint.pprint(json.loads(resp.text))
                print(f"Couldn't react via{reaction_url}'.  See the problem?")
                sys.exit(-1)
            else:
                print(resp.text)

    print(f"Got tasks, type is {type(tasks)}")
    print(tasks.values)
    tasks['channel'] = channels['name'].values[0]
    if tasks.empty:
        print("No new tasks not already reacted to.")
        return

    pprint.pprint(tasks)
    for task in tasks.itertuples():
        print(task)
        genCmd(args, task)
    
# ==============================================================================

if __name__ == "__main__":
    valid_sort_criteria = ["nickname", 
                            "first_name", 
                            "last_name", 
                            "emoji", 
                            "username"]
    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info', 
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line):"+\
                        "(1 server url, (2 team id, (3 auth token, (4 bot name"
                        )

    parser.add_argument('--channel', 
                        '-c',
                        required=True,
                        type=str,
                        help="Channel name(s) from which to get users: "\
                        "-c channel1 channel2. "\
                        "If provided with a list of usernames,"\
                        " this script will pull pull the intersection of users"\
                        " found in the list and those found in both channels."
                        )
    parser.add_argument('--keyword', 
                        '-k',
                        required=False,
                        default="",
                        type=str,
                        help="Keyword to search channel"
                        )      
    parser.add_argument('--message-to-non-responders', 
                        '-n',
                        required=False,
                        default="",
                        type=str,
                        help="File with message (e.g. plain text or markdown)"\
                        " to DM users who did NOT post one of the specified emojis"
                        )  
    parser.add_argument('--message-to-responders', 
                        '-m',
                        required=False,
                        default="",
                        type=str,
                        help="File with message (e.g. plain text or markdown)"\
                        " to DM users who DID post one of the specified emojis"
                        )                         
    parser.add_argument('--username-file', 
                        '-u',
                        required=False,
                        default="",
                        type=str,
                        help="File with all mattermost usernames to report on."\
                        "If provided with a list of channels,"\
                        " will pull intersection of users from each"
                        )                             
    args = parser.parse_args()
    print("Invocation correct!")
    print("Please give me a second to import all these dependencies")

    # Standard library
    import os
    import re
    import sys
    import copy
    import time
    import json
    import pprint
    import requests 
    import concurrent.futures

    from datetime import datetime
    from datetime import date
 
    # Nonstandard libraries
    import pandas as pd

    # Local imports
    from utils import *

    pd.set_option('display.width', 1000)

    all_users = main(args)        

