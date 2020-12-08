import cherrypy
import sqlite3
import os
import datetime
import smtplib
import base64
import ssl
from settings import *
import subprocess

cherrypy.config.update({'log.screen': False,
                        'log.error_file': 'app.log',
                        'log.access_file': ''})


class WebForm:
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as file_data:
            html = file_data.read()
        return html

    @cherrypy.expose
    def submit_page(self, **form_data):
        with open('static/submitted_form.html') as file_data:
            html = file_data.read()
        backend = Backend(form_data)
        backend.write_to_db()
        backend.save_screenshot()
        # backend.send_email()  Temporary disabled.
        return html


class Backend:
    def __init__(self, form_data):
        self.name = form_data['name']
        self.email = form_data['email']
        self.ran_commands = form_data['ran_commands']
        self.produced_output = form_data['produced_output']
        self.screenshot = form_data['screenshot']
        self.expected = form_data['expected']
        self.os_type = form_data['os_type']
        self.has_root = form_data['has_root']
        self.screenshot_filename = self.screenshot.filename.encode('iso-8859-1').decode('utf-8')
        self.cur_time = datetime.datetime.now()
        self.upload_path = os.path.dirname(SCREENSHOTS_DIR)
        self.file_extension = os.path.splitext(self.screenshot.filename)[1]
        self.new_filename = 'screenshot_' + self.cur_time.strftime("%Y-%m-%d_%H-%M-%S") + self.file_extension
        self.uploaded_file = os.path.normpath(os.path.join(self.upload_path, self.new_filename))

    def write_to_db(self):
        values = (self.name, self.email, self.ran_commands, self.produced_output,
                  self.expected, self.os_type, self.has_root, self.screenshot_filename,
                  self.new_filename)
        db = sqlite3.connect(PATH_TO_DB)
        curr_db_conn = db.cursor()
        curr_db_conn.execute("INSERT INTO form_log (name, email, ran_commands, produced_output, expected, os_type, \
                        has_root, original_screenshot_filename, new_screenshot_filename) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        db.commit()
        db.close()

    def save_screenshot(self):
        size = 0
        with open(self.uploaded_file, 'wb') as out:
            while True:
                data = self.screenshot.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)
        cherrypy.log(f"File uploaded as {self.new_filename}, size: {size}, "
                     f"type: {self.screenshot.content_type}.")

    def send_email(self):
        with open(self.uploaded_file, "rb") as file_data:
            file_content = file_data.read()

        # There name is used in the email_template.
        encoded_content = base64.b64encode(file_content)

        with open("email_template.py") as file_data:
            email_template_text = file_data.read()
        email_template = compile(email_template_text, 'email_template.py', 'eval')
        message = eval(email_template)

        if USE_SMTP:
            cherrypy.log("Using smtp credentials.")
            context = ssl.create_default_context()
            try:
                smtp = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.sendmail(SMTP_USER, ADMIN_EMAIL, message)
                cherrypy.log("Email sent successfully.")
            except smtplib.SMTPException as e:
                cherrypy.log(f"Error: unable to send email.\n{e}")
        elif os.path.exists("/usr/sbin/sendmail"):
            cherrypy.log("Using Unix sendmail script.")
            pipe = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                pipe_response = pipe.communicate(message.encode())
                if pipe.returncode != 0:
                    cherrypy.log(f"Sending email failed. Response from subprocess pipeline: "
                                 f"{pipe_response[1]}. Pipeline returns code: {pipe.returncode}.")
            except subprocess.CalledProcessError as e:
                cherrypy.log(f"Error: unable to send email.\n{e}\nReturns code is {pipe.returncode}.")
        else:
            cherrypy.log("Unable to send email. Please set smtp credentials in the config.")


if __name__ == '__main__':
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        cherrypy.log(f"{SCREENSHOTS_DIR} has been created.")
    cherrypy.quickstart(WebForm(), '/', PATH_TO_CONFIG)
