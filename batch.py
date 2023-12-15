import logging
from logging.handlers import TimedRotatingFileHandler
import csv
import chardet
import requests
import json
from emailreport import send_email
from settings import ALMA_SERVER, ALMA_API_KEY, user, log_dir

# batch log
logdir = log_dir  # set the log directory
log_file = logdir + '/batch.log'  # set the log file
batch_log = logging.getLogger('batch')  # create the batch log
batch_log.setLevel(logging.INFO)  # set the batch log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
batch_log.addHandler(file_handler)  # add the file handler to the batch log


def batch(csvfile, almafield):
    filename = csvfile.replace('static/csv', '')  # Set filename for email log
    emailbody = 'Results for {}:\n'.format(filename)  # Initialize email body
    batch_log.info('Processing CSV file: ' + filename)  # Log info

    with open(csvfile) as csv_file:  # Open CSV file
        encoding = chardet.detect(csv_file.read().encode())['encoding']  # Detect encoding

    with open(csvfile, encoding=encoding) as csv_file:  # Open CSV file
        csv_reader = csv.reader(csv_file, delimiter=',')  # Open CSV file for reading
        rownumber = 1  # Initialize row number for email log
        failed = 0  # Initialize failed row counter for email log
        success = 0  # Initialize success row counter for email log

        for row in csv_reader:  # Iterate through each row of the CSV file
            barcode = row[0]  # Column 1 = barcode
            note = row[1]  # Column 2 = value to insert as a note
            batch_log.debug('Processing row ' + str(rownumber) + ': barcode ' + str(barcode) + '; value ' + str(note))

            try:  # Get item record from barcode via requests
                r = requests.get(ALMA_SERVER + '/almaws/v1/items', params={
                    'apikey': ALMA_API_KEY,
                    'item_barcode': barcode,
                    'format': 'json'
                })
                r.raise_for_status()  # Provide for reporting HTTP errors

            except Exception as errh:  # If error...
                emailbody += 'Error finding Barcode ' + str(barcode) + ' in row ' + \
                             str(rownumber) + ': {}\n'.format(errh)
                batch_log.error('Error finding Barcode ' + str(barcode) + ' in row ' +
                                str(rownumber) + ': {}'.format(errh))
                rownumber = rownumber + 1  # Bump the row number up before exiting
                failed = failed + 1
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
                emailbody += 'Error updating Barcode ' + str(barcode) + ' in row ' + \
                             str(rownumber) + ': {}\n'.format(errh)
                batch_log.error('Error updating Barcode ' + str(barcode) + ' in row ' +
                                str(rownumber) + ': {}'.format(errh))
                rownumber = rownumber + 1  # Bump the row number up before exiting
                failed = failed + 1
                continue  # Stop processing this row

            rownumber = rownumber + 1  # Bump the row number up before going to next row
            success = success + 1
            batch_log.debug('Barcode ' + str(barcode) + ' updated in row ' + str(rownumber) + '.')

    # Provide import info as output to command line
    emailbody += str(success) + ' barcodes updated.\n'
    emailbody += str(failed) + ' barcodes not updated.'
    if failed > 0:
        emailbody += ' (See errors above.)'
    batch_log.info('Import complete. ' + str(success) + ' barcodes updated. ' + str(failed) + ' barcodes not updated.')

    # Send email to user
    send_email(emailbody, filename, user)
