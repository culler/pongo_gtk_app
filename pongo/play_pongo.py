from gi.repository import Gtk, WebKit
from urlparse import urlparse, parse_qs
from . import PongoServer

class PlayPongo(Gtk.Window):
    
    def __init__(self, app, pongo_server):
        super(Gtk.Window, self).__init__()
        self.connect("destroy", app.player_destroyed)
        self.scroller = scroller = Gtk.ScrolledWindow()
        self.webview = webview = WebKit.WebView()
        webview.connect("navigation-policy-decision-requested", self.navigate)
        webview.connect("load-error", self.load_error)
        scroller.add(webview)
        self.add(scroller)
        self.load(pongo_server)
        self.set_default_size(900, 600)
        self.show_all()

    def load(self, pongo_server):
        self.pongo_server = pongo_server
        self.set_title('Pongo on %s'%pongo_server.name)
        self.webview.load_uri('http://%s'%pongo_server.ip_address)

    def navigate(self, view, frame, request, action, decision):
        parts = urlparse(request.get_uri())
        if parts.hostname != 'localhost' or parts.port != 8880:
            decision.use()
            return True
        else:
            decision.ignore()
            query_info = parse_qs(parts.query)
            return_page = query_info['state'][0]
            auth_code = query_info['code'][0]
            uri = 'http://%s/spotify_auth/?page=%s;code=%s'%(
                self.pongo_server.ip_address,
                return_page,
                auth_code)
            self.webview.load_uri(uri)
            return False

    def load_error(self, view, frame, uri, error):
        print 'Load Error'
        print 'URI:', uri
        self.webview.load_string("""
        <html>
        <head><title>Error</title></head>
        <body>
        <h1 style="text-align: center;">So Sorry!</h1>
        <h2 style="text-align: center;">We were unable to connect to %s.</h2>
        <div style="text-align: center;">
        <a style="-webkit-appearance: button;
                  text-decoration: none;
                  color: initial;
                  padding: 5px;"
           href="%s">Try again</a>
        </body>
        </html>"""%(self.pongo_server.name, uri), 'text/html', 'UTF-8', '')
        return True
