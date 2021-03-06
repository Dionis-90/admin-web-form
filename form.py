import cherrypy
import sqlite3
import os
import datetime
import smtplib
import base64
import ssl
import subprocess
import string
import random
import requests
from settings import *


cherrypy.config.update({'log.screen': False,
                        'log.error_file': 'app.log',  # TODO: changeable log filename
                        'log.access_file': '',
                        'tools.proxy.on': True,
                        'tools.proxy.local': 'Host', })


class WebForm:
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as file_data:
            html_template = file_data.read()
        html = html_template.format(site_key=RECAPTCHA_SITE_KEY)
        return html

    @cherrypy.expose
    def submit_page(self, **form_data):
        with open('static/submitted_form.html') as file_data:
            success_html = file_data.read()
        backend = Backend(cherrypy.request.remote.ip, form_data)
        is_captcha_success = backend.verify_captcha()
        if is_captcha_success:
            backend.write_to_db()
            backend.save_screenshot()
            backend.send_email()
            return success_html
        elif not is_captcha_success:
            return '<b>Captcha failed.</b>'
        else:
            cherrypy.log('Unexpected error.')
            return '<b>Something went wrong.</b>'


class Backend:
    def __init__(self, client_ip_addr, form_data):
        self.name = form_data['name']
        self.email = form_data['email']
        self.ran_commands = form_data['ran_commands']
        self.produced_output = form_data['produced_output']
        self.screenshot = form_data['screenshot']
        self.expected = form_data['expected']
        self.os_type = form_data['os_type']
        self.has_root = form_data['has_root']
        self.screenshot_filename = self.screenshot.filename.encode('iso-8859-1').decode('utf-8')
        cur_time = datetime.datetime.now()
        uploading_dir = os.path.dirname(SCREENSHOTS_DIR)
        screenshot_file_extension = os.path.splitext(self.screenshot.filename)[1]
        self.new_screenshot_filename = 'screenshot_'+cur_time.strftime("%Y-%m-%d_%H-%M-%S")+screenshot_file_extension
        self.screenshot_file_path = os.path.normpath(os.path.join(uploading_dir, self.new_screenshot_filename))
        self.client_ip_addr = client_ip_addr
        self.recaptcha_token = form_data['g-recaptcha-response']

    def write_to_db(self):
        values = (self.name, self.email, self.ran_commands, self.produced_output,
                  self.expected, self.os_type, self.has_root, self.screenshot_filename,
                  self.new_screenshot_filename, self.client_ip_addr,)
        db = sqlite3.connect(PATH_TO_DB)
        curr_db_conn = db.cursor()
        curr_db_conn.execute("INSERT INTO form_log (name, email, ran_commands, produced_output, expected, os_type, \
                        has_root, original_screenshot_filename, new_screenshot_filename, client_ip_addr) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        db.commit()
        db.close()

    def save_screenshot(self):
        size = 0
        with open(self.screenshot_file_path, 'wb') as out:
            while True:
                data = self.screenshot.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)
        cherrypy.log(f"File uploaded as {self.new_screenshot_filename}, size: {size}, "
                     f"type: {self.screenshot.content_type}.")

    def send_email(self):  # TODO: creating message by email.message module, file attachment none required.
        def generate_marker(length):
            characters = string.ascii_letters+string.digits
            email_marker = ''.join(random.choice(characters) for _ in range(length))
            return email_marker
        with open(self.screenshot_file_path, "rb") as file_data:
            file_content = file_data.read()
        screenshot_in_base64 = base64.b64encode(file_content).decode('ascii')
        with open("email_template.txt") as file_data:
            email_template_text = file_data.read()
        message = email_template_text.format(
            sender_address=SENDER_ADDRESS, admin_email=ADMIN_EMAIL, marker=generate_marker(12),
            base64_file_data=screenshot_in_base64, name=self.name, email=self.email, ran_commands=self.ran_commands,
            produced_output=self.produced_output, expected=self.expected, os_type=self.os_type, has_root=self.has_root,
            screenshot_content_type=self.screenshot.content_type, filename=self.new_screenshot_filename,
            sender_name=SENDER_NAME, subject=SUBJECT, client_ip_addr=self.client_ip_addr, )
        if USE_SMTP:
            cherrypy.log("Using smtp credentials.")
            ssl_context = ssl.create_default_context()
            try:
                if SMTP_USE_SSL:
                    if SMTP_PORT == 465:
                        smtp = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ssl_context)
                    else:
                        cherrypy.log("Using StartTLS.")
                        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                        smtp.starttls()
                else:
                    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.sendmail(SMTP_USER, ADMIN_EMAIL, message.encode('utf-8'))
                smtp.quit()
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

    def verify_captcha(self) -> bool:
        url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {'secret': RECAPTCHA_SECRET,
                'response': self.recaptcha_token}
        response = requests.post(url, data=data)
        return response.json()['success']


if __name__ == '__main__':
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        cherrypy.log(f"{SCREENSHOTS_DIR} has been created.")
    cherrypy.quickstart(WebForm(), '/', PATH_TO_APP_CONFIG)
