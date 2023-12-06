import csv
import requests
import json
from settings import ALMA_SERVER, ALMA_API_KEY


def batch(csvfile, almafield):
    with open(csvfile) as csv_file:  # Open CSV file
        csv_reader = csv.reader(csv_file, delimiter=',')  # Open CSV file for reading
        rownumber = 1  # Initialize row number for error reporting

        for row in csv_reader:  # Iterate through each row of the CSV file
            barcode = row[0]  # Column 1 = barcode
            note = row[1]  # Column 2 = value to insert as a note

            try:  # Get item record from barcode via requests
                r = requests.get(ALMA_SERVER + '/almaws/v1/items', params={
                    'apikey': ALMA_API_KEY,
                    'item_barcode': barcode,
                    'format': 'json'
                })
                r.raise_for_status()  # Provide for reporting HTTP errors

            except Exception as errh:  # If error...
                print('Error finding Barcode ' + str(barcode) + ' in row ' + str(rownumber) + ':', errh)
                rownumber = rownumber + 1  # Bump the row number up before exiting
                continue  # Stop processing this row

            itemrec = r.json()  # If request good, parse JSON into a variable
            itemrec['item_data'][almafield] = note  # Insert column 2 value into the destination field
            headers = {'content-type': 'application/json'}  # Specify JSON content type for PUT request

            # Get IDs from item record for building PUT request endpoint
            mms_id = itemrec['bib_data']['mms_id']  # Bib ID
            holding_id = itemrec['holding_data']['holding_id']  # Holding ID
            item_pid = itemrec['item_data']['pid']  # Item ID

            # Construct API endpoint for PUT request from item record data
            putendpoint = '/almaws/v1/bibs/' + mms_id + '/holdings/' + holding_id + '/items/' + item_pid

            try:  # send full updated JSON item record via PUT request
                r = requests.put(ALMA_SERVER + putendpoint, params={
                    'apikey': ALMA_API_KEY
                }, data=json.dumps(itemrec), headers=headers)
                r.raise_for_status()  # Provide for reporting HTTP errors

            except Exception as errh:  # If error...
                print('Error updating Barcode ' + str(barcode) + ' in row ' + str(rownumber) + ':', errh)
                rownumber = rownumber + 1  # Bump the row number up before exiting
                continue  # Stop processing this row

            rownumber = rownumber + 1  # Bump the row number up before going to next row

    # Provide import info as output to command line
    print('Import complete. All submitted barcodes (except any errors listed above) have been updated in Alma.')
