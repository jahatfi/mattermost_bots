#!/usr/bin/env python3

import requests 
import json
import pprint
import argparse
import pandas as pd
import sys
from utils import *
from datetime import datetime
import time
# ==============================================================================
def main(parser):      
    """
    Provided:
    1. Mattermost server URL,
    2. Team ID,
    3. Authentication token,
    4. bot name,  
    5. File with message,
    6. Channel name
    Post the provided message in the provided channel as this bot
    """                  


    args = parser.parse_args()
    pprint.pprint(args)
    message = ""
    results_per_page = 60 # Can up up to 200

    if not (args.channel or args.user) or (args.channel and args.user):
        print("Must provide exactly --user or --channel option, not none or both")
        sys.exit(-1)

    # Check if files exists

    # First the authenication file
    try:
        with open(args.authentication_info, "r") as authentication_info:
            pass
    except FileNotFoundError as e: 
        print(f"Can't find {args.authentication_info}")
        sys.exit(1)

    creds = parse_creds_from_file(args.authentication_info)
    url, team_id, token, bot_id = creds

    # Next the message file
    try:
        with open(args.message_file, "r") as message_file:
            message = message_file.read()
    except FileNotFoundError as e: 
        print(f"Can't find {args.message_file}")
        sys.exit(1)

    # Get channel by name
    headers = { 
                "is_or_search": "true",
                "time_zone_offset": "0",
                "include_deleted_channels": "false",
                "page": "0",
                "per_page": str(results_per_page),
                "Authorization" : f"Bearer {token}"
            }
    if args.channel:
        channel_url = f"{url}api/v4/teams/{team_id}/channels/name/{args.channel}"
        fail_msg = f"Couldn't create/get channel {args.channel}"

        resp = requests.get(channel_by_name_url, headers=headers)
        # Check for failure
        fail_msg = f"Couldn't create/get channel {args.channel}"
        log_failure_and_exit_if_faile(url, resp, fail_msg)
        # Succeded
        channel_info = json.loads(resp.text)
        channel_id = channel_info['id']
    else:
        # Call below will exit if the GET fails
        user_info_url = f"{url}api/v4/users/username/{args.user}"
        resp = requests.get(user_info_url, headers=headers)
        # Check for failure
        fail_msg = f"Couldn't create/get dm channel {args.channel}"
        log_failure_and_exit_if_failed(url, resp, fail_msg)
        user_id = json.loads(resp.text)['id']
        channel_id  = create_dm_channel(url, bot_id, user_id, headers)

    # Get delay time based on provided value, 0 if none provided.
    delay_seconds = return_computed_delay(args.delay)

    # Post to channel with provided message
    if args.live_run:
        print("Sleeping...")
        sys.stdout.flush()        
        time.sleep(delay_seconds)

        if args.channel:
            print(f"Posting to {args.channel}\nMessage: '{message}'")
        else:
            print(f"DMing {args.user}\nMessage: '{message}'")        
        post_url = url+"api/v4/posts"
        resp = requests.post(post_url, 
                                headers=headers,
                                data=json.dumps({"channel_id": channel_id, 
                                                "message":message}))
        fail_msg = f"Couldn't post/dm {args.channel}{args.user}"
        log_failure_and_exit_if_failed(post_url, resp, fail_msg)

        resp = json.loads(resp.text)
        if args.post_id_file:
            with open(args.post_id_file, "w") as outfile:
                print(f"Writing resulting post ID: {resp['id']} to {args.post_id_file}")
                outfile.write(resp['id'])

    else:
        print("Dry run, not posting anything:")
        if args.channel:
            print(f"Would have posted to {args.channel}\nMessage: '{message}'")
        else:
            print(f"Would have dm'd {args.user}\nMessage: '{message}'")


    print("Done.")
# ==============================================================================
if __name__ == "__main__":
    valid_sort_criteria = ["nickname", "first_name", "last_name", "emoji", "username"]

    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info', 
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line): (1 server url, (2 team id, (3 auth token"
                        )

    parser.add_argument('--channel', 
                        '-c',
                        required=False,
                        type=str,
                        help="Channel name to post in"
                        )   
                        
    parser.add_argument('--message-file', 
                        '-m',
                        required=True,
                        type=str,
                        help="File with message (e.g. plain text or markdown)"
                        )  

    parser.add_argument('--live-run', 
                        '-l',
                        required=False,
                        default=False,
                        type=str2bool,
                        help="Live (True) or dry (False:default) run"
                        )      

    parser.add_argument('--delay', 
                        '-d',
                        required=False,
                        default="",
                        type=str,
                        help="Delay until date/time in format: MM/DD/YYYY: HH:MM"
                        )  
    parser.add_argument('--new-bot-name', 
                        '-b',
                        required=False,
                        default="",
                        type=str,
                        help="Temporary bot display name to use for this execution"
                        )   
    parser.add_argument('--new-bot-icon', 
                        '-i',
                        required=False,
                        default="",
                        type=str,
                        help="Temporary bot display avatar (SVG only)"
                        )  
    parser.add_argument('--post_id_file', 
                        '-p',
                        required=False,
                        default="",
                        type=str,
                        help="Filename to save resulting post ID to."
                        )   
    parser.add_argument('--user', 
                        '-u',
                        required=False,
                        default="",
                        type=str,
                        help="User to DM.  Mututally exclusive with --channel option"
                        )                                                  
    all_users = main(parser)        
