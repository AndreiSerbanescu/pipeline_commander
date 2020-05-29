import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPSenderRefused

class EmailSender:

    def __init__(self, username=None, password=None):

        self.username = username if username is not None else os.environ["EMAIL_USERNAME"]
        self.password = password if password is not None else os.environ["EMAIL_PASSWORD"]

    def send_email(self, receiver_email, subject_name, attachment_fullpath, body=None,
                   backup_pdf_url=None):

        subject_name = str.replace(subject_name, ' ', '-')

        message = MIMEMultipart()
        message["From"]    = self.username
        message["To"]      = receiver_email
        message["Subject"] = f"Report - {subject_name}"

        body = "This is an automatically sent email" if body is None else body
        message.attach(MIMEText(body, "plain"))


        with open(attachment_fullpath, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename= report-{subject_name}.pdf"
        )

        message.attach(part)
        text = message.as_string()

        print("sending email")
        port = 465  # For SSL
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.username, self.password)
            try:
                server.sendmail(self.username, receiver_email, text)
            except SMTPSenderRefused:
                self.__send_backup_mail(backup_pdf_url, port, context, receiver_email, subject_name)

    def __send_backup_mail(self, backup_pdf_url, port, context, receiver_email, subject_name):

        message = MIMEMultipart()
        message["From"]    = self.username
        message["To"]      = receiver_email
        message["Subject"] = f"Report - {subject_name}"

        body = "This is an automatically sent email.\n"

        body += "Unfortunately the PDF report was too large to attach to this email.\n"

        if backup_pdf_url is not None:
            body += f"Please download the PDF report from the following URL \n\n {backup_pdf_url}  \n\n"
            body += "The link will expire in 6 hours."


        message.attach(MIMEText(body, "plain"))
        text = message.as_string()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.username, self.password)
            try:
                server.sendmail(self.username, receiver_email, text)
            except SMTPSenderRefused:
                print("Could not send back-up email")
