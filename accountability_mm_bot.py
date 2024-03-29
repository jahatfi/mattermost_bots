#!/usr/bin/env python3
import argparse
from common import argparse_helpers

# ==============================================================================
def process_reactions(args, reactions, all_users):
    """
    Update the Emoji column of the Pandas Dataframe "all_users" based on the
    provided MatterMost reactions to the specified post.
    """

    #pprint.pprint(reactions)
    for reaction in reactions:
        if args.emoji == "*":
            all_users.loc[all_users['id'] == reaction['user_id'], "Emojis_Response"] += reaction['emoji_name']+"|"
        elif args.emoji == reaction['emoji_name']:
            all_users.loc[all_users['id'] == reaction['user_id'], f"Responded with {args.emoji}?"] = "Yes"
    return all_users
#==============================================================================
def send_dm_to_all_in_df(   user_id,
                            user_name,
                            base_url,
                            bot_id,
                            header,
                            message,
                            bot_name):
    """
    Send dm to all users in the provided dataframe
    """
    print(f"Dm'ing {user_name}")
    channel_id = utils.create_dm_channel(base_url, bot_id, bot_name, user_id, header)
    dm_info = requests.post(base_url+"api/v4/posts",
                                headers=header,
                                data=json.dumps({"channel_id": channel_id, "message":message}))
    dm_info = json.loads(dm_info.text)

    #return dm_info
#==============================================================================
def search_hashtags(args, url, headers, team_id, channels, pages):
    search_url = f"{url}api/v4/teams/{team_id}/posts/search"
    results = pd.DataFrame()
    data = {
        #"is_or_search": False,
        #"time_zone_offset": 0,
        #"include_deleted_channels": True,
        "per_page": 60
    }
    for channel_index, channel_id in enumerate(channels['id'].values):
        get_posts_url = f"{url}api/v4/channels/{channel_id}/posts"
        for page in range(pages):
            print(f"Getting Page {page} of {channels.iloc[channel_index]['name']} posts")
            #headers['page'] = page
            resp = requests.get(   get_posts_url+f"?page={page}",
                                    headers=headers,
                                    data=json.dumps(data)
                                )
            if resp.status_code < 200 or resp.status_code > 299:
                print("Error")
                print(f"URL was '{search_url}'.  See the problem?")
                print(resp.text)

            else:
                posts = json.loads(resp.text)
                messages = pd.DataFrame(posts['posts'], index=None).T
                pprint.pprint(messages['message'])
                #print(messages.columns)
                desired_messages = messages[messages['hashtags'].str.contains(args.keyword)]
                print(f"Found {len(desired_messages)} results")
                if results.empty:
                    results = desired_messages[["id", "create_at", "message", "hashtags"]]
                else:
                    results = results.append(desired_messages[["id", "create_at", "message", "hashtags"]])
                #headers["before"] = posts["prev_post_id"]
                #print(posts["prev_post_id"])
    results = results.reset_index(drop=True)
    pprint.pprint(results)
    return(results)
#==============================================================================
def check_emoji_reactions(  args,
                            url,
                            headers,
                            all_users,
                            bot_id,
                            bot_name,
                            team_name,
                            message_to_non_responders,
                            message_to_responders,
                            sheet_id,
                            post_id
                            ):

    reaction_url = f"{url}/api/v4/posts/{post_id}/reactions"
    resp = requests.get(reaction_url, headers=headers)
    if resp.status_code < 200 or resp.status_code > 299:
        pprint.pprint(json.loads(resp.text))
        print(f"URL was '{reaction_url}'.  See the problem?")
        sys.exit(-1)
    reactions = json.loads(resp.text)

    all_users = process_reactions(args, reactions, all_users)
    all_users.sort_values(args.sort_on, inplace=True)

    with open("csv_log.csv", "a+") as csv_log:
        csv_log.write
        for row in all_users.itertuples():
            # Date, Tasker, Name, response emojis, comments
            # print(row)
            csv_log.write(f"{datetime.today().date()},{args.id},{row.username},{row.emoji},,\n")

    if args.emoji == "*":
        posters = all_users[all_users["Emojis_Response"] != ""]
        print(f"The following {len(posters)} users HAVE posted at least 1 emoji on post {post_id}")
        pprint.pprint(posters[['username', 'first_name', 'last_name']])
    else:
        posters = all_users[all_users[f"Responded with {args.emoji}?"] == "Yes"]
        print(f"The following {len(posters)} users HAVE posted the '{args.emoji}' emoji on post {post_id}")
        pprint.pprint(posters[['username', 'first_name', 'last_name']])

    if args.emoji == "*":
        non_posters = all_users[all_users["Emojis_Response"] == ""]
        print(f"The following {len(non_posters)} users have NOT posted any emoji on post {post_id}")
        pprint.pprint(non_posters[['username', 'first_name', 'last_name']])

    else:
        non_posters = all_users[all_users[f"Responded with {args.emoji}?"] == "No"]
        print(f"The following {len(non_posters)} users have NOT posted the '{args.emoji}' emoji on post {post_id}")
        pprint.pprint(non_posters[['username', 'first_name', 'last_name']])


    leave_indices = non_posters["emoji"].str.contains('|'.join(['palm', 'baby']))
    on_leave = non_posters[leave_indices]
    print(f"The following {len(on_leave)} users are on leave:")
    pprint.pprint(on_leave[['username', 'first_name', 'last_name', 'emoji', 'text']])
    if args.message_non_responders_on_leave:
        print("Including them anyway in list of recipients.")
    else:
        print("Excluding them in non-response message")
        non_posters = non_posters[~leave_indices]

    spreadsheet_updates = {}
    for username in posters['username'].values:
        spreadsheet_updates[username] = "P"
    for username in non_posters['username'].values:
        if username in on_leave['username'].values:
            spreadsheet_updates[username] = "L"
        else:
            spreadsheet_updates[username] = "A"

    #pprint.pprint(spreadsheet_updates)

    # Get the date of the post of interest
    post_url = f"{url}/api/v4/posts/{post_id}"
    resp = requests.get(post_url, headers=headers)
    if resp.status_code < 200 or resp.status_code > 299:
        pprint.pprint(json.loads(resp.text))
        print(f"URL was '{reaction_url}'.  See the problem?")
        sys.exit(-1)
    post_info = pd.DataFrame(json.loads(resp.text))
    #print("Post info:")
    #print(post_info.T)
    post_date = datetime.fromtimestamp(post_info['create_at'].values[0]//1000)
    post_date = post_date.strftime("%Y-%m-%d")

    post_url = f"{url}{team_name}/pl/{post_id}"

    # Log attendence in Google Sheet:
    """
    service = quickstart2.get_service()
    sheet = service.spreadsheets()
    quickstart2.update_attendance(sheet,
                                  sheet_id,
                                  args.tab_name,
                                  spreadsheet_updates,
                                  post_date,
                                  post_url)
    """

    # Send provided DM(s)
    recp_mesg = [[posters, message_to_responders], [non_posters, message_to_non_responders]]
    for recipients, message in recp_mesg:
        if not message or 0 ==  len(recipients):
            continue

        if args.live_run:
            # This happens twice if messaging both groups but that's fine.
            headers['Content-type'] = "application/json"
            # The lists below don't change in content for responders v. non-
            # responders, but they DO change in length.
            headers_list = [headers] * len(recipients)
            base_url_list = [url] * len(recipients)
            bot_id_list = [bot_id] * len(recipients)
            bot_name_list = [bot_name] * len(recipients)
            message_list = [message + f" (Post: {url}{team_name}/pl/{post_id})"] * len(recipients)

            print(f"Live Run: Sending message: '{message_list[0]}'")
            print(f"To {len(recipients)} recipients:")
            pprint.pprint(recipients[['username', 'first_name', 'last_name']])

            with concurrent.futures.ThreadPoolExecutor() as executor:

                executor.map(   send_dm_to_all_in_df,
                                recipients['id'].values,
                                recipients['username'].values,
                                base_url_list,
                                bot_id_list,
                                headers_list,
                                message_list,
                                bot_name_list
                            )
        else:
            print(f"Dry Run: Would send message: '{message}'")
            print(f"To {len(recipients)} recipients:")
            pprint.pprint(recipients[["username", "first_name", "last_name"]])

    return all_users
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
    message_to_responders = ""
    message_to_non_responders = ""

    usernames = []
    creds = utils.parse_creds_from_file(args.authentication_info)
    if len(creds) == 4:
        url, team_id, token, bot_id = creds
    elif len(creds) == 5:
        url, team_id, token, bot_id, sheet_id  = creds

    # Strip any quotes
    url = url.strip('"').strip("'")
    team_id = team_id.strip('"').strip("'")
    token = token.strip('"').strip("'")
    channels = []

    # Print current date + time for log review purposes
    print( str(datetime.now()).center(80, "=") )

    # Next the message file to those who DID respond
    if args.message_to_responders:
        try:
            with open(args.message_to_responders, "r") as message_file:
                message_to_responders = message_file.read()
        except FileNotFoundError as e:
            print(f"Can't find {args.message_to_responders}")
            sys.exit(1)

    # Next message file to those who did NOT respond
    if args.message_to_non_responders:
        try:
            with open(args.message_to_non_responders, "r") as message_file:
                message_to_non_responders = message_file.read()
        except FileNotFoundError as e:
            print(f"Can't find {args.message_to_non_responders}")
            sys.exit(1)

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
        print(f"Cannot find the team {team_id} on this server.")
        print(team_info)
        sys.exit(-1)

    # Get this bot info
    this_bot = utils.get_bot_info(url, bot_id, headers)
    if not this_bot.empty:
        print("Bot metadata:")
        pprint.pprint(this_bot)
    else:
        print(f"It appears that the bot with ID {bot_id} does not exist on {url}")
        sys.exit(-1)

    # Read the file containing the post ID
    if os.path.exists(args.post_id):
        with open(args.post_id, "r") as post_id_file:
            args.post_id = post_id_file.readline().strip()

    # Validate provided channels
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

    # If no user_name file is provided this returns an empty list
    usernames = utils.read_usernames(args.username_file)

    # Return a dataframe of all users - utils.get_users()
    users_url = url + "api/v4/users"
    all_users = utils.get_users(users_url, headers, usernames, channels, results_per_page)
    user_status_url = url + "api/v4/users/status/ids"
    ids = all_users['id'].values.tolist()
    resp = requests.post(user_status_url, headers=headers, data=json.dumps(ids))
    all_users.sort_values("last_name", inplace=True)
    pprint.pprint(all_users)

    # At this point, if no post ID was provided, there's not much else to do.
    if not args.post_id and not args.keyword:
        print("Not post ID or keyword provided. Returning.")
        return
    if args.post_id:
        print(f"Post ID: {args.post_id}")

    # A post ID was provided, so create a new column for all_users and
    # give it a default value
    if args.emoji == "*":
        all_users["Emojis_Response"] = ""
    else:
        all_users[f"Responded with {args.emoji}?"] = "No"

    # Compute sleep time, if any
    if args.delay:
        delay_seconds = utils.return_computed_delay(args.delay)
        if args.live_run:
            sys.stdout.flush()
            time.sleep(delay_seconds)

    # Change the bot name/id if applicable AFTER the sleep, in case
    # another bot changed it while it was sleeping
    if args.new_bot_name:
        if not utils.rename_bot(url,
                                this_bot['username'].values[0],
                                this_bot['user_id'].values[0],
                                args.new_bot_name,
                                headers):
            print("Failed to rename bot; exiting")
            sys.exit(1)
        else:
            print(f"Updated botname to {args.new_bot_name}")
            this_bot['username'] = args.new_bot_name

    # Now (regardless of name update or not) create bot_name for easier reading
    bot_name = this_bot['username']

    """
    if args.new_bot_icon:
        if not update_bot_icon( url,
                                this_bot['username'].values[0],
                                this_bot['user_id'].values[0],
                                args.new_bot_icon,
                                headers):
            print("Exiting")
            sys.exit(1)
    """
    # If a post id is provided,
    if args.post_id:
        all_users = check_emoji_reactions(  args,
                                            url,
                                            headers,
                                            all_users,
                                            bot_id,
                                            bot_name,
                                            team_name,
                                            message_to_non_responders,
                                            message_to_responders,
                                            sheet_id,
                                            args.post_id
                                        )

    # TODO This function below should be in a separate script
    # as it's really a different feature
    if args.keyword:
        if not any(channels):
            print("Please provide at least one channel name")
        else:
            hashtagged_posts = search_hashtags(args,
                                               url,
                                               headers,
                                               team_id,
                                               channels,
                                               3)
            hashtagged_posts.sort_values("create_at", inplace=True)
            #hashtagged_posts['date'] = hashtagged_posts['create_at'].apply(datetime.fromtimestamp)
            hashtagged_posts['date'] = pd.to_datetime(hashtagged_posts["create_at"],
                                                      unit = 'ms')
            #drop one column by name
            hashtagged_posts.drop('create_at', axis=1, inplace=True)

            #start = datetime(1970, 1, 1)  # Unix epoch start time
            #hashtagged_posts['datetime'] = hashtagged_posts['create_at'].apply(lambda x: start + timedelta(seconds=x))
            #hashtagged_posts['string_time'] = hashtagged_posts.datetime.apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
            #print(ts.strftime('%Y-%m-%d %H:%M:%S'))
            pprint.pprint(hashtagged_posts)
            for value in hashtagged_posts['id'].values:
                print(value)
            return hashtagged_posts
# ==============================================================================
if __name__ == "__main__":
    valid_sort_criteria = ["nickname", "first_name", "last_name", "emoji", "username"]

    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info',
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line): (1 server url, (2 team id, (3 auth token, (4 bot name and optionally (5 Google Sheet ID"
                        )
    parser.add_argument('--channels',
                        '-c',
                        nargs='*',
                        type=str,
                        help="Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull the intersection of users from each."
                        )
    parser.add_argument('--post-id',
                        '-p',
                        required=False,
                        default="",
                        type=str,
                        help="ID of post (can be a file with post ID on first line) from which to get reactions.  (Copy the link of the desired post, the ID is the alphanumeric string after the last forward slash)"
                        )
    parser.add_argument('--keyword',
                        '-k',
                        required=False,
                        default="",
                        type=str,
                        help="Keyword to search channel and iterate over matching posts"
                        )
    parser.add_argument('--emoji',
                        '-e',
                        type=str,
                        default="*",
                        help="Name of emoji ('*' for any)"
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
    parser.add_argument('--message-to-non-responders',
                        '-n',
                        required=False,
                        default="",
                        type=str,
                        help="File with message (e.g. plain text or markdown) to DM users who did NOT post one of the specified emojis"
                        )
    parser.add_argument('--message-non-responders-on-leave',
                        required=False,
                        default=False,
                        type=bool,
                        help="Send Non-response message (see -n option) to users even if they ARE on leave."
                        )
    parser.add_argument('--message-to-responders',
                        '-m',
                        required=False,
                        default="",
                        type=str,
                        help="File with message (e.g. plain text or markdown) to DM users who DID post one of the specified emojis"
                        )
    parser.add_argument('--live-run',
                        '-l',
                        required=False,
                        default=False,
                        type=argparse_helpers.str2bool,
                        help="Live (True) or dry (False:default) run"
                        )
    parser.add_argument('--new-bot-name',
                        '-b',
                        required=False,
                        default="",
                        type=str,
                        help="Temporary bot display name to use for this execution"
                        )
    parser.add_argument('--id',
                        '-i',
                        required=False,
                        default="",
                        type=str,
                        help="ID for this tasker"
                        )
    parser.add_argument('--delay',
                        '-d',
                        required=False,
                        default="",
                        type=str,
                        help="Delay until date/time in format: MM/DD/YYYY: HH:MM"
                        )

    parser.add_argument('--sheet-id',
                        type=str,
                        default="",
                        help="ID of Google Sheet"
                        )

    parser.add_argument('--tab-name',
                        '-t',
                        type=str,
                        default="Attendance",
                        help="Name of tab in Google Sheet"
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
    from datetime import datetime, timedelta
    import time
    from common import utils
    import os
    from google_sheets import quickstart2

    all_users = main(args)
    pprint.pprint(all_users)

