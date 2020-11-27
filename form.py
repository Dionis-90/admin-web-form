import cherrypy


class WebForm(object):
    @cherrypy.expose
    def index(self):
        with open('static/form.html') as html:
            return f"""{html.read()}"""

    @cherrypy.expose
    def submit_form(self, name, OSType):
        print(f"Form is submitted {name} and {OSType}.")


if __name__ == '__main__':
    cherrypy.quickstart(WebForm())
