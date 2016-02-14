import sys, signal
from gi.repository import Gtk, Gdk, GObject
from . import PongoServer
from .find_pongo import FindPongo
from .play_pongo import PlayPongo
from .style import css

style = Gtk.CssProvider()
style.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), 
    style,     
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

class PongoApplication(Gtk.Application):
    servers = []
    
    def __init__(self):
        Gtk.Application.__init__(self)
        self.window = None
        self.player = None
                           
    def do_activate(self):
        if not self.window:
            self.window = window = Gtk.ApplicationWindow(application=self,
                                                title="Pongo")
            window.set_size_request(400, 600)
            window.move(75, 50)
            window.set_border_width(10)
            self.finder = finder = FindPongo(self)
            window.add(finder)
        self.window.present()

    def play_pongo(self, server):
        if not self.player:
            self.player = player = PlayPongo(self, server)
            player.move(75, 75)
        else:
            self.player.load(server)
        self.player.show_all()
        self.window.iconify()

    def player_destroyed(self, widget):
        self.shutdown()
        self.quit()
        
    def do_startup(self):
        Gtk.Application.do_startup(self)

    def shutdown(self):
        if self.finder:
            self.finder.shutdown()
        
if __name__ == '__main__':

    GObject.threads_init()
    app = PongoApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    app.shutdown()
    sys.exit(exit_status)
