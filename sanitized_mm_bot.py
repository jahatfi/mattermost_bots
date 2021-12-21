import requests 
import json
import pprint
import argparse
import pandas as pd
import sys
import concurrent.futures
# ==============================================================================
# Reference: https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    """
    Validates that an argparse argument is a boolean value.
    """
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# ==============================================================================
# Reference: https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def valid_sorter(v):
    """
    Validates that argparse sort-on argument is valid value.
    """
    valid_sort_criteria = ["nickname", "first_name", "last_name", "username", "emoji"]
    if v.lower() in valid_sort_criteria:
        return v.lower()

    else:
        print(f"Got {v}")
        raise argparse.ArgumentTypeError(f'Must be one of {valid_sort_criteria}')
# ==============================================================================
def get_channels(base_url, headers):
    """
    Returns a Pandas DataFrame of all channels on this server, but with only
    a subset of the columns that are useful for identifying the channels.
    """
    cols_to_keep = ['id', 'name', 'display_name']
    page = 0
    all_channels = []
    channel_url = base_url+"api/v4/channels"
    
    print(f"Retrieving info for channels, starting with all channels")
    resp = requests.get(channel_url, headers=headers)
    #print(resp.text)
    new_dict = json.loads(resp.text)
    
    all_channels += new_dict


    all_channels = pd.DataFrame(all_channels)
    cols_to_drop = all_channels.columns
    cols_to_drop = list(set(cols_to_drop) - set(cols_to_keep))
    all_channels.drop(cols_to_drop, axis=1, inplace=True)
    #rows_to_keep = all_channels['username'].isin(usernames)
    #all_channels = all_channels[rows_to_keep]
    #pprint.pprint(all_channels)
    return all_channels    
# ==============================================================================
def get_users(users_url, headers, usernames, channels, results_per_page):
    """
    Returns a Pandas DataFrame of all users on this server, but with only
    a subset of the columns that are useful for identifying the users.

    If both usernames and channels_ids provided, return the intersection of the 
    users in both those channels AND the username list.
    Otherwise, if only a list of usernames OR channels is provided,
    return those users.
    """
    cols_to_keep = ['id', 'username', 'email', 'first_name', 'nickname', 'last_name']
    page = 0
    all_users = []
    
    if any(channels):
        for _, channel in channels.iterrows():
            channel_name = channel['name']
            channel_id = channel['id']
            while True:
              
                print(f"Retrieving info for users in channel {channel_name}, page {page} ({results_per_page} entries per page)")
                resp = requests.get(users_url+f"?page={page}&in_channel={channel_id}", headers=headers)
                new_dict = json.loads(resp.text)
                all_users += new_dict
                if len(new_dict) < results_per_page:
                    break
                page += 1

    else:
        while True:
            
            print(f"Retrieving info for users, page {page} ({results_per_page} entries per page)")
            resp = requests.get(users_url+f"?page={page}", headers=headers)
            new_dict = json.loads(resp.text)
            
            all_users += new_dict
            if len(new_dict) < results_per_page:
                break
            page += 1        


    all_users = pd.DataFrame(all_users)
    cols_to_drop = all_users.columns
    cols_to_drop = list(set(cols_to_drop) - set(cols_to_keep))
    all_users.drop(cols_to_drop, axis=1, inplace=True)
    if usernames:
        rows_to_keep = all_users['username'].isin(usernames)
        all_users = all_users[rows_to_keep]
    #pprint.pprint(all_users)
    all_users.drop_duplicates(inplace=True)

    return all_users
# ==============================================================================

def process_reactions(args, reactions, users_url, headers, all_users):
    """
    Update the Emoji column of the Pandas Dataframe "all_users" based on the 
    provided MatterMost reactions to the specified post.
    """

    all_responses = {}
    urls = []
    #pprint.pprint(reactions)
    for reaction in reactions:
        if args.emoji == "*":
            all_users.loc[all_users['id'] == reaction['user_id'], "Emoji Response(s)"] += reaction['emoji_name']+"|"
        elif args.emoji == reaction['emoji_name']:
            all_users[all_users['id'] == reaction['user_id']][f"Responded with {args.emoji}?"] = "Yes"

    return all_users

# ==============================================================================
def dm_user(base_url, username, headers, message, team_id):
    # Start by creating a channel
    new_headers = {
        "team_id": team_id,
        "name": "string",
        "display_name": "Autobot",
        "purpose": "string",
        "header": "DM Between you and autobot",
        "type": "P"
    }
    resp = requests.get(base_url+"api/v4/channels/direct", headers=headers)
# ==============================================================================
def get_bot_info(base_url, bot_name, headers):
    """
    Return bot info for this bot, None if it doesn't exist
    """
    all_bots = requests.get(base_url+"api/v4/bots", headers=headers)
    all_bots = json.loads(all_bots.text)
    all_bots = pd.DataFrame(all_bots)
    #pprint.pprint(all_bots)

    return all_bots[all_bots['username'] == bot_name]
#==============================================================================
def create_dm_channel(base_url, bot_id, user_id, header):
    """
    Return dm channel info between bot and user
    """    
    header['Content-type'] = "application/json"
    channel_info = requests.post(base_url+"api/v4/channels/direct", 
                                headers=header,
                                data=json.dumps([bot_id, user_id]) )
    channel_info = json.loads(channel_info.text)
    return channel_info['id']
#==============================================================================
def send_dm(base_url, channel_id, header, message):
    """
    Send dm to the provided channel
    """    
    header['Content-type'] = "application/json"
    dm_info = requests.post(base_url+"api/v4/posts", 
                                headers=header,
                                data=json.dumps({"channel_id": channel_id, "message":message}))
    dm_info = json.loads(dm_info.text)
    return dm_info

#==============================================================================
def send_dm_to_all_in_df(user_id, user_name, base_url, bot_id, header, message, live_run):
    """
    Send dm to all users in the provided dataframe
    """    
    #user_name = row[1][1]
    #user_id = row[1][0]    
    if not live_run:
        print(f"DRY RUN, send message to: {user_name} {user_id}")
        
    else:

        print(f"LIVE RUN, send message to: {user_name} {user_id}")
        channel_id = create_dm_channel(base_url, bot_id, user_id, header)
        header['Content-type'] = "application/json"
        #print("Firing post")
        dm_info = requests.post(base_url+"api/v4/posts", 
                                    headers=header,
                                    data=json.dumps({"channel_id": channel_id, "message":message}))
        #pprint.pprint(f"dm_info: {dm_info}")
        dm_info = json.loads(dm_info.text)

    #return dm_info
    
# ==============================================================================
def main(parser):      
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
    args = parser.parse_args()
    filter_on_usernames = False
    filter_on_channels = False
    results_per_page = 60 # Can up up to 200

    usernames = []
    with open(args.authentication_info, 'r') as creds_file:
        # Split on '=' in case the format is 'URL: mymattermostserver.com'
        url =     creds_file.readline().split('=')[1].strip()
        team_id = creds_file.readline().split('=')[1].strip()
        token   = creds_file.readline().split('=')[1].strip()
        bot_name = creds_file.readline().split('=')[1].strip()


    # Strip any quotes
    url = url.strip('"').strip("'")
    team_id = team_id.strip('"').strip("'")
    token = token.strip('"').strip("'")

    search_url = f"{url}api/v4/teams/{team_id}/posts/search"
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
    this_bot = get_bot_info(url, bot_name, headers)
    if not this_bot.empty:
        pprint.pprint(this_bot)
        bot_id = this_bot['user_id'].values[0]
    else:
        print(f"It appears that the bot {bot_name} does not exist on {url}")
        sys.exit(-1)


    if args.channels:
        print(args.channels)
        channels = get_channels(url, headers)
        rows_to_keep = channels['name'].isin(args.channels)
        channels = channels[rows_to_keep]
        if channels.empty:
            print(f"Could not find any of the channels provided: {args.channels}")
            print("Exiting.")
            sys.exit(1)        
        filter_on_channels = True
           
    if args.username_file:
        with open(args.username_file, 'r') as callsign_file:
            usernames = callsign_file.readlines()
            usernames = [c.lower().strip() for c in usernames]
    else:
        usernames = []

    users_url = url + "api/v4/users"
    all_users = get_users(users_url, headers, usernames, channels, results_per_page)

    if args.emoji == "*":
        all_users["Emoji Response(s)"] = ""
    else:
        all_users[f"Responded with {args.emoji}?"] = "No"

    reaction_url = f"{url}/api/v4/posts/{args.post_id}/reactions"
    resp = requests.get(reaction_url, headers=headers)
    reactions = json.loads(resp.text)

    all_users  =  process_reactions(args, reactions, users_url, headers, all_users)
    all_users.sort_values(args.sort_on, inplace=True)

    if args.emoji == "*":
        posters = all_users[all_users["Emoji Response(s)"] != ""]
        print(f"The following {len(posters)} users HAVE posted at least 1 emoji on post {args.post_id}")
        pprint.pprint(posters)            
    else:
        posters = all_users[all_users[f"Responded with {args.emoji}?"] == "Yes"]
        print(f"The following {len(posters)} users have NOT posted the '{args.emoji}' emoji on post {args.post_id}")
        pprint.pprint(posters)

    if args.emoji == "*":
        non_posters = all_users[all_users["Emoji Response(s)"] == ""]
        print(f"The following {len(non_posters)} users have NOT posted any emoji on post {args.post_id}")
        pprint.pprint(non_posters)

    else:
        non_posters = all_users[all_users[f"Responded with {args.emoji}?"] == "No"]
        print(f"The following {len(non_posters)} users have NOT posted the '{args.emoji}' emoji on post {args.post_id}")
        pprint.pprint(non_posters)         

    # Send provided DM
    '''
    if args.message_to_non_responders and not non_posters.empty:
        non_posters.apply(send_dm_to_all_in_df, axis=1, args=(url, bot_id, headers, args.message_to_non_responders))

    if args.message_to_responders and not posters.empty:
        posters.apply(send_dm_to_all_in_df, axis=1, args=(url, bot_id, headers, args.message_to_responders+args.post_id))
    '''


    for recipients, message in [[posters, args.message_to_responders], [non_posters, args.message_to_non_responders]]:
        if not message: 
            continue

        these_headers = [headers] * len(recipients)
        live_flag = [args.live_run] * len(recipients)
        base_urls = [url] * len(recipients)
        bot_ids = [bot_id] * len(recipients)

        with concurrent.futures.ThreadPoolExecutor() as executor:

            messages = [message + f" (Post: {url}{team_name}/pl/{args.post_id})"] * len(recipients)
            print(f"Sending message: '{messages[0]}'")

            results = executor.map(   send_dm_to_all_in_df, 
                            recipients['id'].values,
                            recipients['username'].values, 
                            base_urls,
                            bot_ids,
                            these_headers, 
                            messages, 
                            live_flag
                        )

    return all_users

if __name__ == "__main__":
    valid_sort_criteria = ["nickname", "first_name", "last_name", "emoji", "username"]

    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info', 
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line): (1 server url, (2 team id, (3 auth token"
                        )

    parser.add_argument('--channels', 
                        '-c',
                        nargs='*',
                        type=str,
                        help="Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull the intersection of users from each."
                        )

    parser.add_argument('--post-id', 
                        '-p',
                        required=True,
                        type=str,
                        help="ID of post from which to get reactions.  (Copy the link of the desired post, the ID is the alphanumeric string after the last forward slash)"
                        )
    parser.add_argument('--emoji', 
                        '-e',
                        required=True,
                        type=str,
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
                        type=valid_sorter,
                        help=f"Sort results by one of {valid_sort_criteria}, 'username' is the default."
                        )   
    parser.add_argument('--message-to-non-responders', 
                        '-n',
                        required=False,
                        default="",
                        type=str,
                        help="Message to DM users who did NOT post one of the specified emojis"
                        )  
    parser.add_argument('--message-to-responders', 
                        '-m',
                        required=False,
                        default="",
                        type=str,
                        help="Message to DM users who DID post one of the specified emojis"
                        )     
    parser.add_argument('--live-run', 
                        '-l',
                        required=False,
                        default=False,
                        type=str2bool,
                        help="Live (True) or dry (False:default) run"
                        )                                                                               
    all_users = main(parser)        

