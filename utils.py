import argparse
import requests
import json
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
def parse_creds_from_file(authentication_info):
    """
    Parse file with (one per line): 
    (1 server url, 
    (2 team id, 
    (3 auth token, 
    (4 bot name
    Return them all in a tuple
    """
    with open(authentication_info, 'r') as creds_file:
        # Split on '=' in case the format is 'URL: mymattermostserver.com'
        url =     creds_file.readline().split('=')[1].strip()
        team_id = creds_file.readline().split('=')[1].strip()
        token   = creds_file.readline().split('=')[1].strip()
        bot_name = creds_file.readline().split('=')[1].strip()

        return (url, team_id, token, bot_name)
# ==============================================================================
def rename_bot(base_url, old_bot_name, old_bot_id, new_bot_name, headers):
    """
    Rename bot to new name
    """
    payload = {}
    payload["username"] = new_bot_name   
    payload["display_name"] = new_bot_name
    resp = requests.put(base_url+"api/v4/bots/"+old_bot_id, 
                            headers=headers,
                            data=json.dumps(payload))

    
    if resp.status_code < 200 or resp.status_code > 299:
        print(f"Failed to rename {old_bot_name} bot to {new_bot_name}")
        print(resp)
        return False
    else:
        print(f"Renamed {old_bot_name} bot to {new_bot_name}")
    return True
# ==============================================================================
def update_bot_icon(base_url, bot_name, bot_id, new_image_file, headers):
    """
    Update image for bot
    """
    if not new_image_file.endswith(".svg"):
        print(f"Cannot update bot icon with {new_image_file}, file must be .svg")
        return False

    image_data = ""
    with open(new_image_file, "rb") as image_file:
        image_data = image_file.read()
    payload = {"image": image_data}
    resp = requests.put(base_url+"api/v4/bots/"+bot_id+'/'+"icon", 
                        headers=headers,
                        data=json.dumps(payload))

    
    if resp.status_code < 200 or resp.status_code > 299:
        print(f"Failed to update icon {old_bot_name} bot to {new_bot_name}")
        print(resp)    
        return False
    else:
        print(f"Updated image for {bot_name} to {new_image_file}")

    return True