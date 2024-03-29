from flask import current_app
from celery import shared_task
import requests
import chardet
import csv
import json
import smtplib
import email.message


# Celery task
@shared_task
def batch(csvfile, almafield, useremail, key):
    filename = csvfile.replace('app/static/csv/', '')  # Set filename for email log
    emailbody = 'Results for {}:\n'.format(filename)  # Initialize email body

    with open(csvfile) as csv_file:  # Open CSV file
        encoding = chardet.detect(csv_file.read().encode())['encoding']  # Detect encoding

    with open(csvfile, encoding=encoding) as csv_file:  # Open CSV file
        csv_reader = csv.reader(csv_file, delimiter=',')  # Open CSV file for reading
        rownumber = 1  # Initialize row number for email log
        failed = 0  # Initialize failed row counter for email log
        success = 0  # Initialize success row counter for email log
        current_app.logger.info('Processing CSV file: ' + filename)  # Log info

        for row in csv_reader:  # Iterate through each row of the CSV file
            barcode = row[0]  # Column 1 = barcode
            note = row[1]  # Column 2 = value to insert as a note

            current_app.logger.info('Processing barcode {}...'.format(barcode))

            try:  # Get item record from barcode via requests
                r = requests.get(current_app.config['ALMA_SERVER'] + '/almaws/v1/items', params={
                    'apikey': key,
                    'item_barcode': barcode,
                    'format': 'json'
                })
                r.raise_for_status()  # Provide for reporting HTTP errors

            except Exception as errh:  # If error...
                current_app.logger.error('Error finding Barcode ' + str(barcode) + ' in row ' +
                                         str(rownumber) + ': {}'.format(errh))
                emailbody += 'Error finding Barcode ' + str(barcode) + ' in row ' + \
                             str(rownumber) + ': {}\n'.format(errh)
                rownumber = rownumber + 1  # Bump the row number up before exiting
                failed = failed + 1
                continue  # Stop processing this row

            current_app.logger.debug('Barcode {} found.'.format(barcode))

            itemrec = r.json()  # If request good, parse JSON into a variable
            if almafield in value_desc_fields:

                if '|' in note:
                    note = note.split('|')
                    itemrec['item_data'][almafield] = {
                        'value': note[0],
                        'desc': note[1]
                    }

                else:
                    current_app.logger.error('Error updating Barcode ' + str(barcode) + ' in row ' + str(rownumber) +
                                             ': ' + almafield + ' is a value-description field requiring a value \
                                             and a description separated by a pipe (|).')
                    emailbody += 'Error updating Barcode ' + str(barcode) + ' in row ' + str(rownumber) + ': ' + \
                        almafield + ' is a value-description field requiring a value and a description separated by a \
                        pipe (|).\n'
                    rownumber = rownumber + 1  # Bump the row number up before exiting
                    failed = failed + 1
                    continue  # Stop processing this row
            elif almafield in value_fields:
                itemrec['item_data'][almafield] = {'value': note}
            else:
                itemrec['item_data'][almafield] = note  # Insert column 2 value into the destination field
            headers = {'content-type': 'application/json'}  # Specify JSON content type for PUT request

            # Get IDs from item record for building PUT request endpoint
            mms_id = itemrec['bib_data']['mms_id']  # Bib ID
            holding_id = itemrec['holding_data']['holding_id']  # Holding ID
            item_pid = itemrec['item_data']['pid']  # Item ID

            # Construct API endpoint for PUT request from item record data
            putendpoint = '/almaws/v1/bibs/' + mms_id + '/holdings/' + holding_id + '/items/' + item_pid
            current_app.logger.debug('Updating barcode {}...'.format(barcode))

            try:  # send full updated JSON item record via PUT request
                r = requests.put(current_app.config['ALMA_SERVER'] + putendpoint, params={
                    'apikey': key
                }, data=json.dumps(itemrec), headers=headers)
                r.raise_for_status()  # Provide for reporting HTTP errors

            except Exception as errh:  # If error...
                current_app.logger.error('Error updating Barcode ' + str(barcode) + ' in row ' +
                                         str(rownumber) + ': {}'.format(errh))
                emailbody += 'Error updating Barcode ' + str(barcode) + ' in row ' + \
                             str(rownumber) + ': {}\n'.format(errh)
                rownumber = rownumber + 1  # Bump the row number up before exiting
                failed = failed + 1
                continue  # Stop processing this row

            current_app.logger.debug('Barcode {} updated.'.format(barcode))

            rownumber = rownumber + 1  # Bump the row number up before going to next row
            success = success + 1

    # Provide import info as output to command line
    emailbody += str(success) + ' barcodes updated.\n'
    emailbody += str(failed) + ' barcodes not updated.'
    if failed > 0:
        emailbody += ' (See errors above.)'

    # Send email to user
    message = send_email(emailbody, filename, useremail)
    emailbody += '\n' + message  # Add email message to email body

    return emailbody  # Return email body for testing


####################
# Helper functions #
####################

# Send email
def send_email(body, filename, useremail):
    message = email.message.Message()  # create message
    message["Subject"] = 'Results for {}'.format(filename)  # set subject
    message["From"] = current_app.config['SENDER_EMAIL']  # set sender
    message["To"] = useremail  # set recipient
    message.add_header('Content-Type', 'text')  # set content type
    message.set_payload(body)  # set body

    try:  # try to send email
        smtp = smtplib.SMTP(current_app.config['SMTP_ADDRESS'])  # create smtp server
        smtp.sendmail(message['From'], message['To'], message.as_string())  # send email
        smtp.quit()  # quit smtp server
    except Exception as e:  # catch exception
        message = 'Error sending email to {}: '.format(useremail) + '{}'.format(e)  # log error
        current_app.logger.error(message)
    else:  # if no exception
        message = 'Email sent to {}'.format(useremail)  # log info
        current_app.logger.info(message)

    return message  # return message for logging


value_fields = [
    'provenance',
    'break_indicator',
    'pattern_type',
    'alternative_call_number_type',
    'physical_condition',
    'committed_to_retain',
    'retention_reason',
    'process_type',
]

value_desc_fields = [
    'policy',
    'library',
    'location',
    'base_status',
    'physical_material_type',
]
