from gi.repository import Gtk, Gdk, WebKit, Soup
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
    spotify_albums_path = 'spotify/albums'
    spotify_playlists_path = 'spotify/playlists'
    spotify_player_path = 'spotify/queue'
    settings_path = 'pongo/settings'
    
    def __init__(self, app, pongo_server):
        super(Gtk.Window, self).__init__()
        self.app, self.pongo_server = app, pongo_server
        self.set_default_size(432, 768)
        self.search_showing = False
        self.connect("destroy", app.player_destroyed)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.header = header = Gtk.HeaderBar()
        # Black corners on header bar caused by Bug #1437814
        header.set_show_close_button(True)
        header.props.title = pongo_server.name
        back_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_BACK))
        back_button.connect("clicked", self.back_action)
        header.pack_start(back_button)
        app_menu = self._menu()
        menu_button = Gtk.MenuButton(visible=True, direction=Gtk.ArrowType.NONE,
                                         popup=app_menu)
        header.pack_end(menu_button)
        reload_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_REFRESH))
        reload_button.connect("clicked", self.reload_action)
        header.pack_end(reload_button)
        search_button = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_FIND))
        search_button.connect("clicked", self.toggle_search)
        header.pack_end(search_button)
        self.set_titlebar(header)
        self.scroller = scroller = Gtk.ScrolledWindow()
        self.webview = webview = WebKit.WebView()
        webview.connect("navigation-policy-decision-requested", self.navigate)
        webview.connect("load-error", self.load_error)
        self.cookiejar = WebKit.get_default_session().get_feature(Soup.CookieJar)
        scroller.add(webview)
        self.box = box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        box.pack_end(scroller, True, True, 0)
        self.show_all()
        self.base_url = base_url = 'http://%s/'%self.pongo_server.ip_address
        self.webview.load_uri(base_url)
        self.search_box = search_box = Gtk.Box()
        self.search_entry = search = Gtk.Entry(text='Search')
        up = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_UP))
        down = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_DOWN))
        search_box.pack_end(down, False, False, 0)
        search_box.pack_end(up, False, False, 0)
        search_box.pack_end(search, True, True, 0)
        up.connect("clicked", self.search_up)
        down.connect("clicked", self.search_down)

    def _menu(self):
        app_menu = Gtk.Menu()
        # Remove this in "files" mode
        paste_item = Gtk.MenuItem(label="Paste Album")
        paste_item.connect("activate", self.paste_action)
        paste_item.show()
        app_menu.append(paste_item)
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self.settings_action)
        settings_item.show()
        app_menu.append(settings_item)
        connect_item = Gtk.MenuItem(label="Connect")
        connect_item.connect("activate", self.connect_action)
        connect_item.show()
        app_menu.append(connect_item)
        albums_item = Gtk.MenuItem(label="Albums")
        albums_item.connect("activate", self.albums_action)
        albums_item.show()
        app_menu.append(albums_item)
        playlists_item = Gtk.MenuItem(label="Playlists")
        playlists_item.connect("activate", self.playlists_action)
        playlists_item.show()
        app_menu.append(playlists_item)
        player_item = Gtk.MenuItem(label="Player")
        player_item.connect("activate", self.player_action)
        player_item.show()
        app_menu.append(player_item)
        return app_menu
    
    def back_action(self, widget):
        """
        Go back in the WebView history unless the path is /.  In that
        case, open the finder.
        """
        if not self.webview.can_go_back():
            self.app.back_to_finder()
        else:
            self.webview.go_back()

    def reload_action(self, widget):
        """
        Reload the current page.
        """
        self.webview.reload_bypass_cache()

    def toggle_search(self, widget):
        """
        Toggle the visibility of the search box.
        """
        if self.search_showing:
            self.hide_search(widget)
        else:
            self.show_search(widget)
            
    def show_search(self, widget):
        """
        Expose the search box.
        """
        if not self.search_showing:
            self.box.pack_start(self.search_box, False, False, 0)
            self.search_showing = True
            self.show_all()
            
    def hide_search(self, widget):
        """
        Hide the search box.
        """
        if  self.search_showing:
            self.box.remove(self.search_box)
            self.search_showing = False
            self.show_all()
            # BUG: When you search for text, the next matching text
            # gets selected.  I can find no way to clear the selection
            # (except reloading the page).  So the text remains
            # highlighted after the search box is closed.  Clicking on
            # an inactive part of the page will unhighlight the
            # selection, though

    def search_up(self, widget):
        self.webview.search_text(self.search_entry.get_text(),
                                 False, False, True)

    def search_down(self, widget):
        self.webview.search_text(self.search_entry.get_text(),
                                 False, True, True)
        
    def settings_action(self, widget):
        """
        Load the settings page.
        """
        self.webview.load_uri(self.base_url + self.settings_path)

    def paste_action(self, event):
        id = None
        uri = self.clipboard.wait_for_text()
        if uri.startswith('spotify:album:'):
            id = uri.split(':')[2]
        elif uri.startswith('http'):
            path = urlparse(uri).path
            if path.startswith('/album'):
                id = path.split('/')[-1]
        if id:
            self.webview.load_uri(self.base_url + 'spotify/album/%s'%id)

    def connect_action(self, event):
        self.app.back_to_finder()

    def albums_action(self, event):
        self.webview.load_uri(self.base_url + self.spotify_albums_path)

    def playlists_action(self, event):
        self.webview.load_uri(self.base_url + self.spotify_playlists_path)

    def player_action(self, event):
        self.webview.load_uri(self.base_url + self.spotify_player_path)
    
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
            for cookie in self.cookiejar.all_cookies():
                self.cookiejar.delete_cookie(cookie)
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
        <h2 style="text-align: center; font-size: 24px;">Could not connect to %s.</h2>
        <div style="text-align: center;">
        <a style="-webkit-appearance: button;
                  text-decoration: none;
                  color: initial;
                  padding: 5px;"
           href="%s">Try again</a>
        </div>
        </body>
        </html>"""%(self.pongo_server.name, uri), 'text/html', 'UTF-8', '')
        return True
