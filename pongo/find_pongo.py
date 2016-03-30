from gi.repository import Gtk, GObject
from gi.repository import Pango
from threading import Thread
from zeroconf import ServiceBrowser, Zeroconf
from . import PongoServer

"""
Implementation of the FindPongo activity.
"""

class PongoListener(object):
    """
    Listens for services of type _http._tcp whose TXT record specifies path=pongo.
    When such a service is discovered, a row containing its name is added to the
    PongoFinder window.  When the service disappears, the row is removed.
    """
    def __init__(self, finder):
        self.finder = finder
        
    def remove_service(self, zeroconf, service_type, name):
        # We only get the name, not the address, so we are forced to remove
        # all servers with the same name.  Hopefully people will not create
        # multiple servers with the same name.
        for server in self.finder.servers():
            GObject.idle_add(self.finder.remove_server, server)

    def add_service(self, zeroconf, service_type, name):
        server = self.pongo_server(service_type, name, zeroconf)
        if server:
            GObject.idle_add(self.finder.add_server, server)

    def pongo_server(self, service_type, name, zeroconf):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            if info.properties['path'] == '/pongo':
                address = '.'.join([str(ord(c)) for c in info.address]) + ':%s'%info.port
                return PongoServer(info.name.split('.')[0], address)

class PongoServerRow(Gtk.ListBoxRow):
    """
    A row in a listbox displaying the name of a Pongo server.  Hovering over the
    row changes the font-type to bold.  Clicking on the row opens a browser window.
    """
    def __init__(self, server):
        super(Gtk.ListBoxRow, self).__init__()
        self.server = server
        self.label = label = Gtk.Label(server.name)
        self.box = box = Gtk.EventBox()
        box.connect('enter_notify_event', self.mouse_enter)
        box.connect('leave_notify_event', self.mouse_leave)
        box.add(label)
        self.add(box)

    def mouse_enter(self, widget, event, data=None):
        self.label.set_markup('<b>%s</b>'%self.server.name)

    def mouse_leave(self, widget, event, data=None):
        self.label.set_text(self.server.name)
        
class FindPongo(Gtk.Grid):
    """
    A listbox displaying a PongoServerRow for each Pongo server on the local network.
    """
    def __init__(self, app):
        super(Gtk.Grid, self).__init__()
        self.props.row_spacing = 10
        self.app = app
        self.server_list = server_list = app.servers
        self.listbox = listbox = Gtk.ListBox()
        listbox.props.hexpand = True
        listbox.props.halign = Gtk.Align.FILL | Gtk.Align.START
        listbox.props.margin_start = 50
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.connect('row_activated', self.server_select)
        def sort_function(row1, row2, data, notify_destroy):
            return row1.server.name.lower() > row2.server.name.lower()
        listbox.set_sort_func(sort_function, None, False)
        for server in server_list:
            listbox.add(PongoServerRow(server))
        label = Gtk.Label("Local Pongos:")
        label.props.hexpand = True
        label.props.halign = Gtk.Align.FILL | Gtk.Align.START
        self.attach(label, 0, 0, 1, 1)
        self.attach(listbox, 0, 1, 1, 1)
        zeroconf = Zeroconf()
        listener = PongoListener(self)
        self.updater = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        self.show_all()

    def server_select(self, widget, row):
        self.app.play_pongo(row.server)

    def servers(self):
        return [row.server for row in self.listbox.get_children()]
    
    def remove_server(self, server):
        listbox = self.listbox
        for row in listbox.get_children():
            if row.server == server:
                listbox.remove(row)
                break
        listbox.show_all()

    def add_server(self, server):
        listbox = self.listbox
        for row in listbox.get_children():
            if row.server == server:
                return
        listbox.add(PongoServerRow(server))
        listbox.show_all()

    def shutdown(self):
        if self.updater:
            self.updater.cancel()
        self.updater = None
