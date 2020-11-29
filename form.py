import cherrypy
import sqlite3
import os
import datetime


# Define constants
SCREENSHOTS_DIR = 'screenshots/'
PATH_TO_DB = 'db.db'
PATH_TO_CONFIG = 'form.conf'

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
    def submit_page(self, name, email, ran_commands, produced_output, screenshot, expected, os_type, has_root):
        with open('static/submitted_form.html') as file_data:
            html = file_data.read()
        backend = Backend(name, email, ran_commands, produced_output, screenshot, expected, os_type, has_root)
        backend.write_to_db()
        backend.save_screenshot()
        return html


class Backend:
    cur_time = datetime.datetime.now()

    def __init__(self, name, email, ran_commands, produced_output, screenshot, expected, os_type, has_root):
        self.name = name
        self.email = email
        self.ran_commands = ran_commands
        self.produced_output = produced_output
        self.screenshot = screenshot
        self.expected = expected
        self.os_type = os_type
        self.has_root = has_root
        # Make a filename and path
        self.upload_path = os.path.dirname(SCREENSHOTS_DIR)
        self.file_extension = os.path.splitext(screenshot.filename)[1]
        self.upload_new_filename = 'screenshot_' + self.cur_time.strftime("%Y-%m-%d_%H-%M-%S") + self.file_extension
        self.upload_file = os.path.normpath(os.path.join(self.upload_path, self.upload_new_filename))

    def write_to_db(self):
        values = (self.name, self.email, self.ran_commands, self.produced_output,
                  self.expected, self.os_type, self.has_root, self.screenshot.filename,
                  self.upload_new_filename)
        db = sqlite3.connect(PATH_TO_DB)
        curr_db_conn = db.cursor()
        curr_db_conn.execute("INSERT INTO form_log (name, email, ran_commands, produced_output, expected, os_type, \
                        has_root, original_screenshot_filename, new_screenshot_filename) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        db.commit()
        db.close()

    def save_screenshot(self):
        size = 0
        with open(self.upload_file, 'wb') as out:
            while True:
                data = self.screenshot.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)
        cherrypy.log(f'File {self.screenshot.filename} uploaded as {self.upload_new_filename}, size: {size}, \
type: {self.screenshot.content_type}.')


my_form = WebForm()


if __name__ == '__main__':
    cherrypy.quickstart(my_form, '/', PATH_TO_CONFIG)
