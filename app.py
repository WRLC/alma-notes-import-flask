from flask import Flask, render_template, flash
from celery import Celery
from forms import UploadForm
from werkzeug.utils import secure_filename
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import csv
import chardet
import requests
import json
from settings import ALMA_SERVER, ALMA_API_KEY, user_email, log_dir, SECRET_APP_KEY, sender_email, smtp_address
import smtplib
import email.message

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_APP_KEY
app.config['UPLOAD_FOLDER'] = 'static/csv'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# app log
logdir = log_dir  # set the log directory
log_file = logdir + '/app.log'  # set the log file
app_log = logging.getLogger('app')  # create the batch log
app_log.setLevel(logging.INFO)  # set the batch log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
app_log.addHandler(file_handler)  # add the file handler to the batch log


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # File
        file = form.csv.data  # Get the CSV file from the form
        filename = secure_filename(file.filename)  # Make the filename safe, even though it should be safe already
        file.save(os.path.join(  # Save the file to the CSV folder in the instance path
            app.config['UPLOAD_FOLDER'], filename
        ))

        # Field
        field = form.almafield.data  # Get the Alma field from the form

        # Run the batch function on the CSV file
        task = batch.delay(
            os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            ), field
        )

        # Provide import info as message to user
        flash(
            'The CSV "' + filename + '" is being processed (taskid = ' + str(
                task.id) + '). An email will be sent to {} when complete.'.format(user_email),
            'info'
        )

    return render_template('upload.html', form=form)


@celery.task
def batch(csvfile, almafield):
    filename = csvfile.replace('static/csv', '')  # Set filename for email log
    emailbody = 'Results for {}:\n'.format(filename)  # Initialize email body
    app_log.info('Processing CSV file: ' + filename)  # Log info

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
            app_log.debug('Processing row ' + str(rownumber) + ': barcode ' + str(barcode) + '; value ' + str(note))

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
                app_log.error('Error finding Barcode ' + str(barcode) + ' in row ' +
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
                app_log.error('Error updating Barcode ' + str(barcode) + ' in row ' +
                              str(rownumber) + ': {}'.format(errh))
                rownumber = rownumber + 1  # Bump the row number up before exiting
                failed = failed + 1
                continue  # Stop processing this row

            rownumber = rownumber + 1  # Bump the row number up before going to next row
            success = success + 1
            app_log.debug('Barcode ' + str(barcode) + ' updated in row ' + str(rownumber) + '.')

    # Provide import info as output to command line
    emailbody += str(success) + ' barcodes updated.\n'
    emailbody += str(failed) + ' barcodes not updated.'
    if failed > 0:
        emailbody += ' (See errors above.)'
    app_log.info('Import complete. ' + str(success) + ' barcodes updated. ' + str(failed) + ' barcodes not updated.')

    # Send email to user
    send_email(emailbody, filename, user_email)


def send_email(body, filename, useremail):
    message = email.message.Message()  # create message
    message["Subject"] = 'Results for {}'.format(filename)  # set subject
    message["From"] = sender_email  # set sender
    message["To"] = useremail  # set recipient
    message.add_header('Content-Type', 'text')  # set content type
    message.set_payload(body)  # set body

    try:  # try to send email
        smtp = smtplib.SMTP(smtp_address)  # create smtp server
        smtp.sendmail(message['From'], message['To'], message.as_string())  # send email
        smtp.quit()  # quit smtp server
    except Exception as e:  # catch exception
        app_log.error('Error sending email to {}: '.format(useremail) + '{}'.format(e))  # log error
    else:  # if no exception
        app_log.info('Email sent to {}'.format(useremail))  # log info


if __name__ == '__main__':
    app.run()
