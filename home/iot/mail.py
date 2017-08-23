import smtplib
from email.mime.text import MIMEText


class Mail:
    def __init__(self, smtp_server: str, smtp_port: int = 25, smtp_username: str = "", smtp_password: str = ""):
        self.smtp_password = smtp_password
        self.smtp_username = smtp_username
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, subject: str, mail_to: str, mail_from: str, body: str):
        # Adapted from http://stackoverflow.com/a/8321609/1974978
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['To'] = mail_to
        msg['From'] = mail_from
        mail = smtplib.SMTP(self.smtp_server, self.smtp_port)
        mail.starttls()
        mail.login(self.smtp_username, self.smtp_password)
        mail.sendmail(mail_from, mail_to, msg.as_string())
        mail.quit()
