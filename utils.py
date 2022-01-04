import argparse


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
