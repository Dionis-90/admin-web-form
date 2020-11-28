import cherrypy
import sqlite3
import os


class WebForm(object):
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as html:
            return f"""{html.read()}"""

    @cherrypy.expose
    def submit_form(self, name, email, ran_commands, produced_output, screenshot, expected, os_type, has_root):
        print(f"Form is submitted by {name} and {os_type}.")
        values = (name, email, ran_commands, produced_output, expected, os_type, has_root)
        db = sqlite3.connect("db.db")
        curr_db_conn = db.cursor()
        curr_db_conn.execute("INSERT INTO form_log \
        (name, email, ran_commands, produced_output, expected, os_type, has_root) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
        db.commit()
        db.close()
        upload_path = os.path.dirname('screenshots/')
        upload_filename = screenshot.filename
        upload_file = os.path.normpath(
            os.path.join(upload_path, upload_filename))
        size = 0
        print(upload_file)
        with open(upload_file, 'wb') as out:
            while True:
                data = screenshot.file.read(8192)
                if not data:
                    break
                out.write(data)
                size += len(data)
        out = '''
        File received.
        Filename: {}
        Length: {}
        Mime-type: {}
        '''.format(screenshot.filename, size, screenshot.content_type, data)
        return out


if __name__ == '__main__':
    cherrypy.quickstart(WebForm())
