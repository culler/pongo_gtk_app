from gi.repository import Gtk, WebKit
from urlparse import urlparse, parse_qs
from . import PongoServer

"""
Implementation of the PlayPongo activity.
"""

class PlayPongo(Gtk.Window):
    """
    A WebView window connected to a Pongo server.  This WebView traps connections
    to localhost:8800, which is the redirect address used by Spotify authentication
    for the Pongo Spotify app.
    """
    def __init__(self, app, pongo_server):
        super(Gtk.Window, self).__init__()
        self.app, self.pongo_server = app, pongo_server
        self.connect("destroy", app.player_destroyed)
        self.header = header = Gtk.HeaderBar()
        # Black corners on header caused by Bug #1437814
        header.set_show_close_button(True)
        header.props.title = pongo_server.name
        back_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_BACK))
        back_button.connect("clicked", self.back_action)
        header.pack_start(back_button)
        settings_menu = Gtk.Menu()
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self.settings_action)
        settings_item.show()
        settings_menu.append(settings_item)
        menu_button = Gtk.MenuButton(visible=True, direction=Gtk.ArrowType.NONE,
                                         popup=settings_menu)
        header.pack_end(menu_button)
        reload_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REFRESH))
        reload_button.connect("clicked", self.reload_action)
        header.pack_end(reload_button)
        self.set_titlebar(header)
        self.scroller = scroller = Gtk.ScrolledWindow()
        self.webview = webview = WebKit.WebView()
        webview.connect("navigation-policy-decision-requested", self.navigate)
        webview.connect("load-error", self.load_error)
        scroller.add(webview)
        self.add(scroller)
        self.base_url = base_url = 'http://%s/'%self.pongo_server.ip_address
        self.webview.load_uri(base_url)
        self.set_default_size(900, 600)
        self.show_all()
        
    def back_action(self, widget):
        """
        Go back in the WebView history unless the path is /.  In that
        case, open the finder.
        """
        parts = urlparse(self.webview.get_uri())
        if parts.path == "/":
            self.app.back_to_finder()
        else:
            self.webview.go_back()

    def reload_action(self, widget):
        """
        Reload the current page.
        """
        self.webview.reload_bypass_cache()

    def settings_action(self, widget):
        """
        Load the settings page.
        """
        self.webview.load_uri(self.base_url + 'pongo/settings')
            
    def navigate(self, view, frame, request, action, decision):
        """
        Watch for the redirect address from Spotify authentication.
        When found redirect the redirect to the spotify_auth view on
        the Pongo server.
        """
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
        """
        Custom error screen to display when the http connection fails.
        """
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
