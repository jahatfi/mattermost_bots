#!/usr/bin/env python3
import argparse
from common import argparse_helpers

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
    or in the case of a specific emoji, show those who have NOT reacted with that emoji.
    """
    results_per_page = 60 # Can up up to 200

    usernames = []
    creds = utils.parse_creds_from_file(args.authentication_info)
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
    #print(f"team url: {team_url}")

    team_info = requests.get(team_url, headers=headers)
    if team_info.status_code == 200:
        team_info = json.loads(team_info.text)
        team_name = team_info["name"]
        #print(team_name)
        #pprint.pprint(team_info)
    else:
        print(f"Cannot find the team {team_name} on this server.")
        print(team_info)
        sys.exit(-1)

    # Get this bot info
    this_bot = utils.get_bot_info(url, bot_id, headers)
    if not this_bot.empty:
        pprint.pprint(this_bot)
    else:
        print(f"It appears that the bot with ID {bot_id} does not exist on {url}")
        sys.exit(-1)

    if args.channels:
        channels = pd.DataFrame()
        channel_url = url+f"api/v4/teams/{team_id}/channels/search"
        payload = {}

        for channel in args.channels:
            payload["term"] = channel
            resp = requests.post(channel_url, headers=headers, data=json.dumps(payload))
            if resp.status_code >= 200 and resp.status_code < 400:
                channels = channels.append(pd.DataFrame(json.loads(resp.text)))
            else:
                print(f"Couldn't find channel {channel}")

        if channels.empty:
            print(f"Can't find any channels that match any of {args.channels}")
            sys.exit(1)
        channels = channels[['id', 'name']]
        print("All matching channels:")
        pprint.pprint(channels)
        filter_on_channels = True

    if args.username_file:
        with open(args.username_file, 'r') as callsign_file:
            usernames = callsign_file.readlines()
            usernames = [c.lower().strip() for c in usernames]
    else:
        usernames = []

    users_url = url + "api/v4/users"
    all_users = utils.get_users(users_url, headers, usernames, channels, results_per_page)
    user_status_url = url + "api/v4/users/status/ids"
    ids = all_users['id'].values.tolist()
    resp = requests.post(user_status_url, headers=headers, data=json.dumps(ids))
    if resp.status_code >= 200 and resp.status_code <= 399:
        status = pd.DataFrame(json.loads(resp.text))
        status = status.rename(columns={'user_id':'id'})

        all_users = all_users.merge(status[['id', 'status', 'manual']], on='id', how="left")
    else:
        print(resp.text)
    all_users.insert(0, "Date", '')
    all_users['Date'] = str(datetime.now())
    all_users.sort_values(args.sort_on, inplace=True)

    #pprint.pprint(all_users)

    need_headers = False
    try:
        with open(args.log_file, 'r') as _:
            print("File exists")
    except FileNotFoundError as e:
        print("No file found")
        need_headers = True

    with open(args.log_file, "a+", newline='') as log:
        log_lines = all_users.to_csv(index=False, header=need_headers)
        for line in log_lines:
            log.write(line)

        print("First line")
        pprint.pprint(log_lines[0:2])

    print(f"Appended data to {args.log_file}", )

# ==============================================================================
if __name__ == "__main__":
    valid_sort_criteria = ["nickname", "first_name", "last_name", "emoji", "username"]

    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info',
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line): (1 server url, (2 team id, (3 auth token, (4 bot name"
                        )

    parser.add_argument('--channels',
                        '-c',
                        nargs='*',
                        type=str,
                        help="Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull the intersection of users from each."
                        )

    parser.add_argument('--username-file',
                        '-u',
                        required=False,
                        default="",
                        type=str,
                        help="File with all mattermost usernames to report on.  If provided with a list of channels, will pull intersection of  from each"
                        )
    parser.add_argument('--sort-on',
                        '-s',
                        default="username",
                        type=argparse_helpers.valid_sorter,
                        help=f"Sort results by one of {valid_sort_criteria}, 'username' is the default."
                        )

    parser.add_argument('--log-file',
                        '-f',
                        default="log.csv",
                        type=str,
                        help=f"File to append logs to."
                        )
    args = parser.parse_args()

    print("Invocation correct!")
    print("Please give me a second to import all these dependencies")
    import requests
    import json
    import pprint
    import pandas as pd
    import sys
    import concurrent.futures
    from datetime import datetime
    import time
    from common import utils
    import os

    all_users = main(args)

