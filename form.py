import cherrypy
import sqlite3


class WebForm(object):
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as html:
            return f"""{html.read()}"""

    @cherrypy.expose
    def submit_form(self, name, email, ran_commands, produced_output, file, expected, os_type, has_root):
        print(f"Form is submitted by {name} and {os_type}.")
        values = (name, email, ran_commands, produced_output, expected, os_type, has_root)
        DB = sqlite3.connect("db.db")
        curr_db_conn = DB.cursor()
        curr_db_conn.execute("INSERT INTO form_log \
        (name, email, ran_commands, produced_output, expected, os_type, has_root) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
        DB.commit()
        DB.close()
        with open("screenshots/file", 'w') as f:
            f.write(file)


if __name__ == '__main__':
    cherrypy.quickstart(WebForm())
