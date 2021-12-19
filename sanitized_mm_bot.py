import requests 
import json
import pprint
import argparse
import pandas as pd
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
    Validates that argparse sort-method argument is valid value.
    """
    valid_sort_criteria = ["nickname", "first_name", "last_name", "username", "emoji"]
    if v.lower() in valid_sort_criteria:
        return v.lower()

    else:
        print(f"Got {v}")
        raise argparse.ArgumentTypeError(f'Must be one of {valid_sort_criteria}')

# ==============================================================================
def get_users(users_url, headers, usernames):
    """
    Returns a Pandas DataFrame of all users on this server, but with only
    a subset of the columns that are useful for identifying the users.
    """
    cols_to_keep = ['id', 'username', 'email', 'first_name', 'nickname', 'last_name']
    page = 0
    all_users = []

    while True:
        
        print(f"Retrieving info for users, page {page} (60 entries per page)")
        resp = requests.get(users_url+f"?page={page}", headers=headers)
        new_dict = json.loads(resp.text)
        
        all_users += new_dict
        if len(new_dict) < 60:
            break
        page += 1

    all_users = pd.DataFrame(all_users)
    cols_to_drop = all_users.columns
    cols_to_drop = list(set(cols_to_drop) - set(cols_to_keep))
    all_users.drop(cols_to_drop, axis=1, inplace=True)
    rows_to_keep = all_users['username'].isin(usernames)
    all_users = all_users[rows_to_keep]
    #pprint.pprint(all_users)
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
        elif args.emoji_name == reaction['emoji_name']:
            all_users[all_users['id'] == reaction['user_id']][f"Responded with {args.emoji}?"] = "Yes"

    return all_users
# ==============================================================================
def main(parser):      
    """
    Provided:
    1. Mattermost server URL,
    2. Authentication tokens, 
    3. List of Mattermost usernames,
    4. An emoji (or '*' for any emoji),
    Show which users from the list of usernames provided have reacted to the 
    specific post with any emoji ('*'), or the specified emoji, 
    as well as all users who have NOT posted any emoji ('*'), or in the case of 
    a specific emoji, show those who have NOT reacted with that emoji.
    """                                              
    args = parser.parse_args()
    #pprint.pprint(args)

    usernames = []
    token = #TODO
    url = # TODO
    team_id = #TODO
    search_url = f"{url}api/v4/teams/{team_id}/posts/search"
    headers = { 
                "is_or_search": "true",
                "time_zone_offset": "0",
                "include_deleted_channels": "true",
                "page": "0",
                "per_page": "60",
                # TODO Include authorization token below
                "Authorization" : "Bearer TODO"
            }

    with open(args.username_file, 'r') as callsign_file:
        usernames = callsign_file.readlines()
    usernames = [c.lower().strip() for c in usernames]
    users_url = url + "api/v4/users"

    all_users = get_users(users_url, headers, usernames)
    if args.emoji == "*":
        all_users["Emoji Response(s)"] = ""
    else:
        all_users[f"Responded with {args.emoji}?"] = "No"

    reaction_url = f"{url}/api/v4/posts/{args.post_id}/reactions"
    resp = requests.get(reaction_url, headers=headers)
    reactions = json.loads(resp.text)

    all_users  =  process_reactions(args, reactions, users_url, headers, all_users)
    all_users.sort_values(args.sort_method, inplace=True)

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

    return all_users

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

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
                        type=str,
                        help="File with all mattermost usernames"
                        )
    parser.add_argument('--sort-method', 
                        '-s',
                        default="username",
                        type=valid_sorter,
                        help="Sort results by 'username' (default), 'callsign', 'first' or 'last' name"
                        )           
    all_users = main(parser)        