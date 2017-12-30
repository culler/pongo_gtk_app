import sys, signal, socket
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
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
            window.set_default_size(768, 768)
            window.move(75, 50)
            window.set_border_width(30)
            box = Gtk.Box(Gtk.Orientation.VERTICAL, 10)
            box.set_homogeneous(False)
            self.finder = finder = FindPongo(self)
            box.pack_start(finder, True, True, 0)
            box.set_orientation(Gtk.Orientation.VERTICAL)
            gobox = Gtk.Box(Gtk.Orientation.HORIZONTAL, 10)
            gobox.set_homogeneous(False)
            self.IPentry = IPentry = Gtk.Entry()
            go = Gtk.Button(None, image=Gtk.Image(stock=Gtk.STOCK_GO_FORWARD))
            go.connect('clicked', self.ip_connect)
            gobox.pack_end(go, False, False, 0)
            gobox.pack_end(IPentry, True, True, 0)
            box.pack_end(gobox, False, False, 0)
            label = Gtk.Label("IP Address/Name:")
            label.props.halign=Gtk.Align.START
            box.pack_end(label, False, False, 0)
            window.add(box)
            box.show_all()
        self.window.present()

    def ip_connect(self, event):
        data = self.IPentry.get_text()
        try:
            longs, shorts, addrs = socket.gethostbyaddr(data)
            if not shorts:
                name = longs.split('.')[0]
            else:
                name = shorts[0]
            server = PongoServer(name=name, ip_address=addrs[0]+':8880')
            self.play_pongo(server)
        except (socket.herror, IndexError):
            self.IPentry.set_text('unknown')
        
    def play_pongo(self, server):
        self.player = PlayPongo(self, server)
        self.player.move(75, 50)
        self.player.show_all()
        self.window.iconify()

    def player_destroyed(self, widget):
        if self.restore_finder:
            self.restore_finder = False
        else:
            self.quit_app()
        
    def back_to_finder(self):
        self.window.present()
        self.restore_finder = True
        self.player = None
            
    def do_startup(self):
        Gtk.Application.do_startup(self)

    def quit_app(self, widget=None):
        if self.finder:
            self.finder.shutdown()
        self.quit()
        
def main():
    GObject.threads_init()
    app = PongoApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    app.quit_app()
    sys.exit(exit_status)

if __name__ == '__main__':
    main()
