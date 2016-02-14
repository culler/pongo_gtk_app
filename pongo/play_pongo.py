from gi.repository import Gtk, WebKit
from . import PongoServer

class PlayPongo(Gtk.Window):
    
    def __init__(self, app, pongo_server):
        super(Gtk.Window, self).__init__()
        self.connect("destroy", app.player_destroyed)
        self.scroller = scroller = Gtk.ScrolledWindow()
        self.webview = webview = WebKit.WebView()
        scroller.add(webview)
        self.add(scroller)
        self.load(pongo_server)
        self.set_default_size(900, 600)
        self.show_all()

    def load(self, pongo_server):
        self.set_title('Pongo on %s'%pongo_server.name)
        self.webview.load_uri('http://%s'%pongo_server.ip_address)
