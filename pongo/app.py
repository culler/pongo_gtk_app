import sys, signal
from gi.repository import Gtk, Gdk, GObject
from . import PongoServer
from .find_pongo import FindPongo
from .style import css

style = Gtk.CssProvider()
style.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), 
    style,     
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)
                     
class PongoApplication(Gtk.Application):
    _servers = []
    
    def __init__(self):
        Gtk.Application.__init__(self)
        self.window = None
        self.grid = None
                           
    def do_activate(self):
        if not self.window:
            self.window = window = Gtk.ApplicationWindow(application=self,
                                                title="Pongo")
            window.set_size_request(400, 600)
            window.set_border_width(10)
            self.find_pongo = find_pongo = FindPongo(self._servers)
            window.add(find_pongo)
        self.window.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def shutdown(self):
        self.find_pongo.shutdown()
        
if __name__ == '__main__':
    
    GObject.threads_init()
    app = PongoApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    app.shutdown()
    sys.exit(exit_status)
