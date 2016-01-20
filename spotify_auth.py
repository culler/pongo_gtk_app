#import sys
import webbrowser
import spotipy
from urllib import urlopen
from spotipy import oauth2
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Event
from urlparse import urlparse, parse_qs

PORT = 8880
PONGO_CLIENT_ID='1a8a214ef5b04390bf61cf269dee8555'
PONGO_CLIENT_SECRET='4267117b389d468a87dc0bc880f2c014'
SCOPE = 'user-library-read'
username = 'culler'

class PongoGetHandler(BaseHTTPRequestHandler):
    """
    Wait for a request and respond with a simple message.
    """
    message = """<html>
<head><title>Pongo</title></head>
<body>
<h1>Spotify authorization succeeded for %s.</h1>
</body>
</html>
"""
    timeout_message = """<html>
<head><title>Pongo</title></head>
<body>
<h1>The login process timed out.  Please try again.</h1>
</body>
</html>
"""
    error_message = """<html>
<head><title>Pongo</title></head>
<body>
<h1>Spotify authorization failed.</h1>
</body>
</html>
"""

    def do_GET(self):
        """ One-shot GET handler for our little http server."""
        query_info = parse_qs(urlparse(self.path).query)
        state = query_info.get('state', [None])[0]
        if 'stop' in query_info:
            message = self.timeout_message
        elif state:
            message = self.message%state
        else:
            message = self.error_message
        self.server.query_info = query_info
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)

    def log_request(self, code, size=0):
        pass

class AuthThread(Thread):
    """This thread runs an http server on PORT, waiting for the redirect
    from the spotify auth server.
    """
    query_info = None
    
    def run(self):
        """Start a one-shot http server and wait for the redirect."""
        server = HTTPServer(('', PORT), PongoGetHandler)
        server.handle_request()
        self.query_info = server.query_info

    def stop(self):
        """To stop the thread, send it a special http request."""
        response = urlopen('http://localhost:%d/?stop=YES'%PORT)
        

class Spotify(spotipy.Spotify):
    def authenticate(self):
        sp_oauth = oauth2.SpotifyOAuth(PONGO_CLIENT_ID,
                                       PONGO_CLIENT_SECRET,
                                       'http://localhost:%d/'%PORT,
                                       state='pongo_name_2',
                                       scope=SCOPE,
                                       cache_path=".cache-" + username )
        token_info = sp_oauth.get_cached_token()
        if not token_info:
            print 'Web authorization required:'
            auth_thread = AuthThread()
            auth_thread.start()
            print 'http server thread started'
            auth_url = sp_oauth.get_authorize_url()
            webbrowser.open(auth_url)
            print 'waiting for redirect'
            auth_thread.join(60)
            if not auth_thread.query_info:
                print 'Timed out'
                auth_thread.stop()
                return
            query_info = auth_thread.query_info
            print 'Received authorization for:', query_info['state'][0]
            code = auth_thread.query_info.get('code')[0]
            token_info = sp_oauth.get_access_token(code)
        else:
            print 'Using cached credentials:' 
        print 'Access:', token_info['access_token']
        print 'Refresh:', token_info['refresh_token']
        print 'TimeToLive:', token_info['expires_in']
        print 'Scope:', token_info['scope']
        self._auth = token_info['access_token']

if __name__ == '__main__':
    spotify = Spotify()
    spotify.authenticate()
    album = spotify.current_user_saved_albums()['items'][0]['album'] 
    print album['id'], album['name']
    
