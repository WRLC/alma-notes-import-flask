import logging
from logging.handlers import TimedRotatingFileHandler
from settings import log_dir, sender_email, smtp_address
import smtplib
import email.message

# scheduler log
logdir = log_dir  # set the log directory
log_file = logdir + '/email.log'  # set the log file
email_log = logging.getLogger('email')  # create the scheduler log
email_log.setLevel(logging.INFO)  # set the scheduler log level
file_handler = TimedRotatingFileHandler(log_file, when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(  # set the file handler format
    logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %H:%M:%S'
    ))
email_log.addHandler(file_handler)  # add the file handler to the scheduler log


def send_email(body, filename, user):
    message = email.message.Message()  # create message
    message["Subject"] = 'Results for {}'.format(filename)  # set subject
    message["From"] = sender_email  # set sender
    message["To"] = user  # set recipient
    message.add_header('Content-Type', 'text')  # set content type
    message.set_payload(body)  # set body

    try:  # try to send email
        smtp = smtplib.SMTP(smtp_address)  # create smtp server
        smtp.sendmail(message['From'], message['To'], message.as_string())  # send email
        smtp.quit()  # quit smtp server
    except Exception as e:  # catch exception
        email_log.error('Error sending email to {}: '.format(user) + '{}'.format(e))  # log error
    else:  # if no exception
        email_log.info('Email sent to {}'.format(user))  # log info
