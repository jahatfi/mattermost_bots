print("Import modules...")

import pickle
import os.path
import argparse
import pprint
import json
from collections import OrderedDict

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
print("Done")

# If modifying these scopes, delete the file token.pickle.
#SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive"]
#===============================================================================
def colnum_string(n):
    """
    Convert column number to column namte
    Source: https://stackoverflow.com/questions/23861680
    """

    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string
#===============================================================================
def get_first_free_row(sheet, sheet_id, tab_name):
    """
    Return the number of the first free (blank) row
    Row data is returned as a list of individual lists, e.g.
    [[],[],[]]
    """

    range = tab_name + "!A3:A"

    # Call the Sheets API
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=range).execute()
    values = result.get('values', [])
    print(values)
    first_free_row = len(values)+3
    print("First free row is: ")
    print(first_free_row)
    return first_free_row

#===============================================================================
def get_first_free_col(sheet, sheet_id, tab_name):
    """
    Return the name of the first free (blank) col
    Column data is returned as one list containing one list
    [[]]
    """
    range = tab_name + "!A2:2"

    # Call the Sheets API
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=range).execute()

    # Get the first and only child list returned
    values = result.get('values', [])[0]
    first_free_col = len(values)+1
    first_free_col = colnum_string(first_free_col)
    print("First Free Column:")
    print(first_free_col)
    return first_free_col
#===============================================================================
def returned_ordered_callsigns(sheet, sheet_id, tab_name):
    """
    Return the ordered list of callsigns in the callsign column,
    including blanks if there are any.  This is important, as the order
    might change due to users sorting it, adding new names,
    removing old ones, etc.
    """

    # First find the "Callsign" column
    range = tab_name + "!A2:2"
    key = "Callsign"
    ordered_callsigns = []
    # Call the Sheets API
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=range).execute()

    # Get the first and only child list returned
    values = result.get('values', [])[0]

    print(values)

    # Add one b/c Google sheets index starting at 1
    col_num = values.index(key)+1

    # Found the column with callsigns, grab the whole column minues the header
    col_name = colnum_string(col_num)
    range = tab_name + "!" + col_name + "1:" + col_name

    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=range).execute()

    values = result.get('values', [])

    # Create a dictionary mapping callsign to row number
    ordered_callsigns = [""]*len(values)
    for value_index, value in enumerate(values):
        # Value index is the row number, value is the callsign
        # Some cells might be blank
        if value:
            ordered_callsigns[value_index] = value[0]
    return ordered_callsigns

#===============================================================================
def update_attendance(sheet, # Type: googleapiclient.discovery.Resource'
                      sheet_id:str,
                      tab_name:str,
                      attendence:dict,
                      date:str,
                      event_name:str):
    """
    Given a Google Sheet, name of the tab with attendance info,
    attendance info (dictionary mapping call signs to attendance info, e.g.
    {
        "bob": "Y",
        "joe": "Y",
        "sue": "Leave",
        "buzz": "Excused"
    }
    )
    Update the spreadsheet
    """
    attendence = {k: v for k, v in sorted(attendence.items(),
                                          key=lambda x: x[1])}

    #print(attendence)
    col_to_insert = get_first_free_col(sheet, sheet_id, tab_name)
    ordered_callsigns = returned_ordered_callsigns(sheet, sheet_id, tab_name)
    # Sort the name to row mapping in numerical order
    #pprint.pprint(ordered_callsigns)
    range = tab_name + "!" + col_to_insert + "1:" + col_to_insert
    #print("Print it all")
    updates = [[date], [event_name]]
    for callsign_index, callsign in enumerate(ordered_callsigns[2:]):
        if callsign in attendence:
            entry = [attendence[callsign]]
        else:
            entry = [""]
        updates.append(entry)
        print(f"{callsign_index+2} {callsign} '{entry}'")

    #pprint.pprint(updates)
    body = {}
    body["values"] = updates
    body['majorDimension'] = "ROWS"
    body["range"] = range

    #print(f"Range: {range}")
    #print(help(sheet.values().update))

    result = sheet.values().update(spreadsheetId=sheet_id,
                                   range=range,
                                   valueInputOption="RAW",
                                   body=body).execute()
    if result['updatedCells'] == len(updates):
        print(f"Sucessfully updated {len(updates)} cells in Google Sheet")
    else:
        print("Error: Didn't update all cells:")
        print(len(updates))
        pprint.pprint(result)
#===============================================================================
def main(args):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = args.sheet_id
    SAMPLE_RANGE_NAME = 'A!A2:E'


    service = get_service()

    try:
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=args.sheet_id,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            for row in values:
                pass
                # Print columns A and E, which correspond to indices 0 and 4.
                #print('%s, %s' % (row[0], row[4]))
    except HttpError as err:
        print(err)

    #get_first_free_row(sheet, args.sheet_id, args.tab_name)
    #get_first_free_col(sheet, args.sheet_id, args.tab_name)
    #print("Getting callsign mapping")
    #mapping = returned_ordered_callsigns(sheet, args.sheet_id, args.tab_name)
    #pprint.pprint(mapping)

    update_attendance(sheet, args.sheet_id, args.tab_name, {}, "3/17/2022", "PT")
#===============================================================================
def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials-sheets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service
#===============================================================================

if __name__ == '__main__':

    # Create the parser and add arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--sheet-id',
                        '-s',
                        type=str,
                        default="",
                        help="ID of Google Sheet"
                        )

    parser.add_argument('--tab-name',
                        '-t',
                        type=str,
                        default="Attendance",
                        help="Name of tab in sheet"
                        )

    args = parser.parse_args()
    main(args)