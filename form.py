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


class WebForm(object):
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as html:
            return html.read()

    @cherrypy.expose
    def submit_form(self, name, email, ran_commands, produced_output, screenshot, expected, os_type, has_root):

        # Make a filename and path
        upload_path = os.path.dirname(SCREENSHOTS_DIR)
        file_extension = os.path.splitext(screenshot.filename)[1]
        cur_time = datetime.datetime.now()
        upload_new_filename = 'screenshot_'+cur_time.strftime("%Y-%m-%d_%H-%M-%S")+file_extension
        upload_file = os.path.normpath(os.path.join(upload_path, upload_new_filename))

        # Write form data to the DB
        values = (name, email, ran_commands, produced_output, expected, os_type, has_root, screenshot.filename,
                  upload_new_filename)
        db = sqlite3.connect(PATH_TO_DB)
        curr_db_conn = db.cursor()
        curr_db_conn.execute("INSERT INTO form_log (name, email, ran_commands, produced_output, expected, os_type, \
                has_root, original_screenshot_filename, new_screenshot_filename) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        db.commit()
        db.close()

        # Write file to local storage
        size = 0
        with open(upload_file, 'wb') as out:
            while True:
                data = screenshot.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)
        cherrypy.log(f'File {screenshot.filename} uploaded as {upload_new_filename}, size: {size}, \
type: {screenshot.content_type}.')
        with open('static/submitted_form.html') as html:
            return html.read()


my_form = WebForm()


if __name__ == '__main__':
    cherrypy.quickstart(my_form, '/', PATH_TO_CONFIG)
