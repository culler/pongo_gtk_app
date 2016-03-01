import sys, signal
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
gi.require_version('Gst', '1.0')
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
        self.restore_finder = False
                           
    def do_activate(self):
        if not self.window:
            self.window = window = Gtk.ApplicationWindow(application=self,
                                                title="Pongo")
            window.connect("destroy", self.quit_app)
            window.set_name("finderWindow")
            window.set_default_size(432, 768)
            window.move(75, 50)
            window.set_border_width(10)
            self.finder = finder = FindPongo(self)
            window.add(finder)
        self.window.present()

    def play_pongo(self, server):
        self.player = player = PlayPongo(self, server)
        player.move(75, 75)
        player.show_all()
        self.window.iconify()

    def player_destroyed(self, widget):
        if self.restore_finder:
            self.restore_finder = False
        else:
            self.quit_app()
        
    def back_to_finder(self):
        self.window.present()
        self.restore_finder = True
        self.player.destroy()
        self.player = None
            
    def do_startup(self):
        Gtk.Application.do_startup(self)

    def quit_app(self, widget=None):
        if self.finder:
            self.finder.shutdown()
        self.quit()
        
if __name__ == '__main__':

    GObject.threads_init()
    app = PongoApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    app.quit_app()
    sys.exit(exit_status)
