from gi.repository import Gtk, Gdk, WebKit, Soup
from urlparse import urlparse, parse_qs
from . import PongoServer
import re

"""
Implementation of the PlayPongo activity.
"""
spotify = 'https://open.spotify.com'
album_uri = re.compile('spotify:album:([A-z0-9/\+-_]{22})')
album_link = re.compile(spotify + '/album/([A-z0-9/\+-_]{22})')
playlist_uri = re.compile('spotify:user:[^:]*:playlist:([A-z0-9/\+-_]{22})')
playlist_link = re.compile(spotify + '/user/[^:]*/playlist/([A-z0-9/\+-_]{22})')
                             
class PlayPongo(Gtk.Window):
    """
    A WebView window connected to a Pongo server.  This WebView traps connections
    to localhost:8800, which is the redirect address used by Spotify authentication
    for the Pongo Spotify app, as well as urls with path of the form /pongo/*, which
    are consumed as commands to the app itself.
    """
    album_paste_path = 'album/paste/'
    playlist_paste_path = 'playlist/paste/'
    
    def __init__(self, app, pongo_server):
        super(Gtk.Window, self).__init__(title='Pongo')
        self.app, self.pongo_server = app, pongo_server
        self.set_default_size(432, 768)
        self.search_showing = False
        self.connect("destroy", app.player_destroyed)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
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
        self.search_box = search_box = Gtk.Box()
        self.search_entry = search = Gtk.Entry(text='Find')
        search.connect("key-release-event", self.key_action)
        up = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_UP))
        down = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_DOWN))
        search_box.pack_end(down, False, False, 0)
        search_box.pack_end(up, False, False, 0)
        search_box.pack_end(search, True, True, 0)
        up.connect("clicked", self.search_up)
        down.connect("clicked", self.search_down)
        self.album_paste_url = self.base_url + self.album_paste_path
        self.playlist_paste_url = self.base_url + self.playlist_paste_path
        self.webview.load_uri(self.base_url + 'albums')

    def navigate(self, view, frame, request, action, decision):
        """
        Controls navigation through the Pongo pages.
        """
        url = request.get_uri()
        parts = urlparse(url)
        # Handle Spotify authentication redirects
        if parts.hostname == 'localhost' and parts.port == 8880:
            for cookie in self.cookiejar.all_cookies():
                if cookie.get_domain().endswith('spotify.com'):
                    self.cookiejar.delete_cookie(cookie)
            query_info = parse_qs(parts.query)
            return_page = query_info['state'][0]
            auth_code = query_info['code'][0]
            url = 'http://%s/spotify_auth/?page=%s;code=%s'%(
                self.pongo_server.ip_address,
                return_page,
                auth_code)
            self.webview.load_uri(url)
            decision.ignore()
            return False
        # Handle app commands
        path = parts.path
        if path.startswith('/pongo/'):
            command = path.split('/')[-1]
            if command == 'paste_link':
                url = self.get_paste_url()
                if url:
                    self.webview.load_uri(url)
            elif command == 'connect':
                self.app.back_to_finder()
            elif command == 'search':
                self.toggle_search()
            decision.ignore()
            return False
        decision.use()
        return True

    def toggle_search(self):
        """
        Toggle the visibility of the search box.
        """
        if self.search_showing:
            self.hide_search()
        else:
            self.show_search()
            
    def show_search(self):
        """
        Expose the search box.
        """
        if not self.search_showing:
            self.box.pack_start(self.search_box, False, False, 0)
            self.search_showing = True
            self.show_all()
            self.search_entry.grab_focus()
            self.search_entry.select_region(0, -1);
            
    def hide_search(self):
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
        
    def key_action(self, widget, event, data=None):
        if event.keyval == Gdk.KEY_Return:
            self.search_down(widget)
            
    def get_paste_url(self):
        id = None
        uri = self.clipboard.wait_for_text()
        if id is None:
            match = album_uri.match(uri)
            if match:
                id = match.group(1)
                uri_type = 'album'
        elif id is None:
            match = album_link.match(uri)
            if match:
                id = match.group(1)
                uri_type = 'album'
        elif id is None:
            match = playlist_uri.match(uri)
            if match:
                id = match.group(1)
                uri_type = 'playlist'
        elif id is None:
            match = playlist_link.match(uri)
            if match:
                id = match.group(1)
                uri_type = 'playlist'
        if id is not None and uri_type == 'album':
            return self.album_paste_url + id
        elif id is not None and uri_type == 'playlist':
            return self.playlist_paste_url + id
        else:
            dialog = Gtk.MessageDialog(
                self, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                "The clipboard did not contain a valid Spotify link.")
            dialog.run()
            dialog.destroy()
            

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
