import sys
from gi.repository import Gtk
from .find_pongo import FindPongoWindow

class PongoApplication(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        win = FindPongoWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

app = PongoApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
