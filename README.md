A number of bots for automatically managing and tracking tasks for team members
on a Mattermost server using the Mattermost v4 API.  Also allows for updating
Google Sheets with accountability/attendance information.

Important Note:

The `-a` flag is mandatory, and must look like this (the last line is optional):
```
url = https://yourmattermostserver.com/
team_id = yourMattermostTeamId
token = yourMattermostToken
bot_id = yourMattermostBotId
sheet_id = googleSheetID # Optional
```

1. post_or_dm_as_bot.py - Does what it says on the can:

```
python post_or_dm_as_bot.py -h
usage: post_or_dm_as_bot.py [-h] --authentication-info AUTHENTICATION_INFO [--channel CHANNEL] --message-file MESSAGE_FILE [--live-run LIVE_RUN] [--delay DELAY]
                            [--new-bot-name NEW_BOT_NAME] [--new-bot-icon NEW_BOT_ICON] [--post_id_file POST_ID_FILE] [--user USER]

optional arguments:
  -h, --help            show this help message and exit
  --authentication-info AUTHENTICATION_INFO, -a AUTHENTICATION_INFO
                        File with (one per line): (1 server url, (2 team id, (3 auth token
  --channel CHANNEL, -c CHANNEL
                        Channel name to post in
  --message-file MESSAGE_FILE, -m MESSAGE_FILE
                        File with message (e.g. plain text or markdown)
  --live-run LIVE_RUN, -l LIVE_RUN
                        Live (True) or dry (False:default) run
  --delay DELAY, -d DELAY
                        Delay until date/time in format: MM/DD/YYYY: HH:MM
  --new-bot-name NEW_BOT_NAME, -b NEW_BOT_NAME
                        Temporary bot display name to use for this execution
  --new-bot-icon NEW_BOT_ICON, -i NEW_BOT_ICON
                        Temporary bot display avatar (SVG only)
  --post_id_file POST_ID_FILE, -p POST_ID_FILE
                        Filename to save resulting post ID to.
  --user USER, -u USER  User to DM. Mututally exclusive with --channel option
```
2. get_user_status.py - Get a table of users, including their first and last
   names, as well as Mattermost status (e.g. offline, away, etc)
```
python get_user_status.py -h
usage: get_user_status.py [-h] --authentication-info AUTHENTICATION_INFO [--channels [CHANNELS [CHANNELS ...]]] [--username-file USERNAME_FILE] [--sort-on SORT_ON]
                          [--log-file LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --authentication-info AUTHENTICATION_INFO, -a AUTHENTICATION_INFO
                        File with (one per line): (1 server url, (2 team id, (3 auth token, (4 bot name
  --channels [CHANNELS [CHANNELS ...]], -c [CHANNELS [CHANNELS ...]]
                        Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull the intersection
                        of users from each.
  --username-file USERNAME_FILE, -u USERNAME_FILE
                        File with all mattermost usernames to report on. If provided with a list of channels, will pull intersection of from each
  --sort-on SORT_ON, -s SORT_ON
                        Sort results by one of ['nickname', 'first_name', 'last_name', 'emoji', 'username'], 'username' is the default.
  --log-file LOG_FILE, -f LOG_FILE
                        .csv File to append logs to.
```
3. accountability_mm_bot.py - Retrieve all emojis for a given post, and
    optionally do any of the following:
    3.1 Send a message to everyone (can provide a list of usernames or message only members of specific channels) who reacted with an emoji
    3.2 Send a message to everyone (can provide a list of usernames or message only members of specific channels) who did NOT react with an emoji
    3.3 Update a Google Sheet with the same info (who responded and who didn't)
```
python accountability_mm_bot.py -h
Import modules...
Done
usage: accountability_mm_bot.py [-h] --authentication-info AUTHENTICATION_INFO [--channels [CHANNELS [CHANNELS ...]]] [--post-id POST_ID] [--keyword KEYWORD]
                                [--emoji EMOJI] [--username-file USERNAME_FILE] [--sort-on SORT_ON] [--message-to-non-responders MESSAGE_TO_NON_RESPONDERS]
                                [--message-to-responders MESSAGE_TO_RESPONDERS] [--live-run LIVE_RUN] [--new-bot-name NEW_BOT_NAME] [--id ID] [--delay DELAY]
                                [--sheet-id SHEET_ID] [--tab-name TAB_NAME]

optional arguments:
  -h, --help            show this help message and exit
  --authentication-info AUTHENTICATION_INFO, -a AUTHENTICATION_INFO
                        File with (one per line): (1 server url, (2 team id, (3 auth token, (4 bot name
  --channels [CHANNELS [CHANNELS ...]], -c [CHANNELS [CHANNELS ...]]
                        Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull the intersection
                        of users from each.
  --post-id POST_ID, -p POST_ID
                        ID of post (can be a file with post ID on first line) from which to get reactions. (Copy the link of the desired post, the ID is the
                        alphanumeric string after the last forward slash)
  --keyword KEYWORD, -k KEYWORD
                        Keyword to search channel and iterate over matching posts
  --emoji EMOJI, -e EMOJI
                        Name of emoji ('*' for any)
  --username-file USERNAME_FILE, -u USERNAME_FILE
                        File with all mattermost usernames to report on. If provided with a list of channels, will pull intersection of from each
  --sort-on SORT_ON, -s SORT_ON
                        Sort results by one of ['nickname', 'first_name', 'last_name', 'emoji', 'username'], 'username' is the default.
  --message-to-non-responders MESSAGE_TO_NON_RESPONDERS, -n MESSAGE_TO_NON_RESPONDERS
                        File with message (e.g. plain text or markdown) to DM users who did NOT post one of the specified emojis
  --message-to-responders MESSAGE_TO_RESPONDERS, -m MESSAGE_TO_RESPONDERS
                        File with message (e.g. plain text or markdown) to DM users who DID post one of the specified emojis
  --live-run LIVE_RUN, -l LIVE_RUN
                        Live (True) or dry (False:default) run
  --new-bot-name NEW_BOT_NAME, -b NEW_BOT_NAME
                        Temporary bot display name to use for this execution
  --id ID, -i ID        ID for this tasker
  --delay DELAY, -d DELAY
                        Delay until date/time in format: MM/DD/YYYY: HH:MM
  --sheet-id SHEET_ID   ID of Google Sheet
  --tab-name TAB_NAME, -t TAB_NAME
                        Name of tab in sheet
```
4. read_mentions.py - Under construction.  Plan is for it to be able to
   search a channel for messages that @ the name of this bot, parse a
   well-formatted tasker from the post, react to the post to acknowledge reciept
   and create a new accountability task for that post.  In other words, non-bot
   owners could create new accountable tasks. It needs a little more
   work and testing.
   ```
   python read_mentions.py -h
usage: read_mentions.py [-h] --authentication-info AUTHENTICATION_INFO --channel CHANNEL [--keyword KEYWORD] [--live-run LIVE_RUN]
                        [--message-to-non-responders MESSAGE_TO_NON_RESPONDERS] [--message-to-responders MESSAGE_TO_RESPONDERS] [--username-file USERNAME_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --authentication-info AUTHENTICATION_INFO, -a AUTHENTICATION_INFO
                        File with (one per line):(1 server url, (2 team id, (3 auth token, (4 bot name
  --channel CHANNEL, -c CHANNEL
                        Channel name(s) from which to get users: -c channel1 channel2. If provided with a list of usernames, this script will pull pull the
                        intersection of users found in the list and those found in both channels.
  --keyword KEYWORD, -k KEYWORD
                        Keyword to search channel
  --live-run LIVE_RUN, -l LIVE_RUN
                        Live (True) or dry (False:default) run
  --message-to-non-responders MESSAGE_TO_NON_RESPONDERS, -n MESSAGE_TO_NON_RESPONDERS
                        File with message (e.g. plain text or markdown) to DM users who did NOT post one of the specified emojis
  --message-to-responders MESSAGE_TO_RESPONDERS, -m MESSAGE_TO_RESPONDERS
                        File with message (e.g. plain text or markdown) to DM users who DID post one of the specified emojis
  --username-file USERNAME_FILE, -u USERNAME_FILE
                        File with all mattermost usernames to report on.If provided with a list of channels, will pull intersection of users from each

   ```