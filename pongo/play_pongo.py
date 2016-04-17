from gi.repository import Gtk, Gdk, WebKit, Soup
from urlparse import urlparse, parse_qs
from . import PongoServer

"""
Implementation of the PlayPongo activity.
"""

class TabBar(Gtk.Box):
    def __init__(self, tabnames, initial, action):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self.action = action
        self.tabs = []
        for name in tabnames:
            button = Gtk.ToggleButton(name)
            button.connect("toggled", self._handle_click, len(self.tabs))
            self.tabs.append(button)
            self.pack_start(button, True, True, 0)
        self.ignore = True
        self.active_tab = initial
        self.tabs[initial].set_active(True)
            
    def _handle_click(self, button, index):
        if self.ignore:
            self.ignore = False
            return
        if index == self.active_tab:
            self.ignore = True
            button.set_active(True)
        else:
            old_active = self.tabs[self.active_tab]
            self.active_tab = index
            self.ignore = True
            old_active.set_active(False)
        self.action(index)
                             
class PlayPongo(Gtk.Window):
    """
    A WebView window connected to a Pongo server.  This WebView traps connections
    to localhost:8800, which is the redirect address used by Spotify authentication
    for the Pongo Spotify app.
    """
    albums_path = 'albums'
    paste_path = 'spotify/album/paste'
    playlists_path = 'playlists'
    player_path = 'player'
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
        back_button = Gtk.Button.new_from_icon_name("go-previous",
                                                    Gtk.IconSize.SMALL_TOOLBAR)
        back_button.connect("clicked", self.back_action)
        header.pack_start(back_button)
        settings_button = Gtk.Button.new_from_icon_name("preferences-system",
                                                        Gtk.IconSize.SMALL_TOOLBAR)
        settings_button.connect("clicked", self.settings_action)
        header.pack_end(settings_button)
        paste_button = Gtk.Button.new_from_icon_name("edit-paste",
                                                     Gtk.IconSize.SMALL_TOOLBAR)
        paste_button.connect("clicked", self.paste_action)
        header.pack_end(paste_button)
        search_button = Gtk.Button.new_from_icon_name("edit-find",
                                                      Gtk.IconSize.SMALL_TOOLBAR)
        search_button.connect("clicked", self.toggle_search)
        header.pack_end(search_button)
        self.set_titlebar(header)
        self.scroller = scroller = Gtk.ScrolledWindow()
        self.webview = webview = WebKit.WebView()
        webview.connect("navigation-policy-decision-requested", self.navigate)
        webview.connect("load-error", self.load_error)
        self.cookiejar = WebKit.get_default_session().get_feature(Soup.CookieJar)
        scroller.add(webview)
        tab_bar = TabBar(['Playlists', 'Albums', 'Player'], 1, self.tab_action)
        self.box = box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        box.pack_end(scroller, True, True, 0)
        box.pack_end(tab_bar, False, False, 0)
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
        self.albums_url = self.base_url + self.albums_path
        self.album_item_url = None
        self.playlists_url = self.base_url + self.playlists_path
        self.playlist_item_url = None
        self.player_url = self.base_url + self.player_path

    def navigate(self, view, frame, request, action, decision):
        """
        Controls navigation through the Pongo pages.
        """
        url = request.get_uri()
        parts = urlparse(url)
        if parts.hostname == 'localhost' and parts.port == 8880:
            # Handle Spotify authentication redirects
            decision.ignore()
            for cookie in self.cookiejar.all_cookies():
                self.cookiejar.delete_cookie(cookie)
            query_info = parse_qs(parts.query)
            return_page = query_info['state'][0]
            auth_code = query_info['code'][0]
            url = 'http://%s/spotify_auth/?page=%s;code=%s'%(
                self.pongo_server.ip_address,
                return_page,
                auth_code)
            self.webview.load_uri(url)
            return False
        # App navigation:
        # We remember the state (list or detail) of the Albums and Playlist tabs.
        # To navigate up from the detail view to the list view, use the back
        # button. 
        decision.use()
        segments = parts.path.split('/')
        if len(segments) > 0:
            head = segments[1]
            if head == 'album':
                self.album_item_url = url
            elif head == 'playlist':
                self.playlist_item_url = url
        return True

    def tab_action(self, index):
        if index == 0:
            if self.playlist_item_url:
                target = self.playlist_item_url
            else:
                target = self.playlists_url
        elif index == 1:
            if self.album_item_url:
                target = self.album_item_url
            else:
                target = self.albums_url
        elif index == 2:
            target = self.player_url
        self.webview.load_uri(target)

    def go_up(self):
        url = self.webview.get_uri();
        parts = urlparse(url)
        segments = parts.path.split('/')
        if (len(segments) > 1):
            head = segments[1]
            if head == "album":
                self.album_item_url = None
                self.webview.load_uri(self.albums_url)
                return True;
            elif head == "playlist":
                self.playlist_iem_url = None
                self.webview.load_uri(self.playlists_url)
                return True
        return False;
        
    def back_action(self, widget):
        """
        Go up one level.
        """
        if not self.go_up():
            self.app.back_to_finder()

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
            self.webview.load_uri(self.base_url + '%s/%s'%(
                self.spotify_paste_path, id))

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
