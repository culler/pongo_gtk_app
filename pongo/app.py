import sys, signal
from gi.repository import Gtk, Gdk, GObject
from . import PongoServer
from .find_pongo import PongoServerList

style = Gtk.CssProvider()

css = """
GtkWindow, GtkLabel, GtkListBox {
  background-color: #ffffff;
  font-size: 16px;
}
"""
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
        signal.signal(signal.SIGINT, self.control_C_handler)
                           
    def add_server(self, server):
        if server not in self._servers:
            self._servers.append(server)
        
    def do_activate(self):
        if not self.window:
            self.window = window = Gtk.ApplicationWindow(application=self,
                                                title="Pongo")
            window.set_size_request(400, 600)
            window.set_border_width(10)
            self.grid = grid = Gtk.Grid()
            grid.props.row_spacing = 10
            window.add(grid)
            self.find_pongo = find_pongo = PongoServerList(self._servers)
            grid.attach(Gtk.Label("Select a local Pongo:"), 0, 0, 1, 1)
            grid.attach(find_pongo, 0, 1, 1, 1)
            grid.show_all()
        self.window.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def shutdown(self):
        self.find_pongo.shutdown()

    def control_C_handler(self, signum, frame):
        self.shutdown()
        self.quit()
        
if __name__ == '__main__':
    
    GObject.threads_init()
    app = PongoApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
