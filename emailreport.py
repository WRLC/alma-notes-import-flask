import logging
from logging.handlers import TimedRotatingFileHandler
from settings import log_dir, sender_email, smtp_address
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    message = MIMEMultipart("alternative")  # create message
    message["Subject"] = 'Results for ', filename  # set subject
    message["From"] = sender_email  # set sender

    # Create the plain-text and HTML version of your message
    text = body

    html = """\
            <html>
              <body>
                <div>""" + body + """</div>
              </body>
            </html>
            """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    message["To"] = user  # set recipient

    try:  # try to send email
        smtp = smtplib.SMTP(smtp_address)  # create smtp server
        smtp.sendmail(sender_email, user, message.as_string())  # send email
        smtp.quit()  # quit smtp server
    except Exception as e:  # catch exception
        email_log.error('Error sending email to {}: {}'.format(user, str(e)))  # log error
    else:  # if no exception
        email_log.info('Email sent to %s' % user)  # log info
