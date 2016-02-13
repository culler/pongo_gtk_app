from gi.repository import Gtk, GObject
from gi.repository import Pango
from threading import Thread
from zeroconf import ServiceBrowser, Zeroconf
from . import PongoServer

class PongoListener(object):
    def __init__(self, server_list):
        self.server_list = server_list
        
    def remove_service(self, zeroconf, service_type, name):
        GObject.idle_add(self.server_list.remove_server,
                         self.pongo_server(service_type, name, zeroconf))
        
    def add_service(self, zeroconf, service_type, name):
        GObject.idle_add(self.server_list.add_server,
                         self.pongo_server(service_type, name, zeroconf))

    def pongo_server(self, service_type, name, zeroconf):
        info = zeroconf.get_service_info(service_type, name)
        address = '.'.join([str(ord(c)) for c in info.address]) + ':%s'%info.port
        return PongoServer(info.name, address)

class PongoServerRow(Gtk.ListBoxRow):
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
        
class PongoServerList(Gtk.ListBox):
    def __init__(self, server_list):
        super(Gtk.ListBox, self).__init__()
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.server_list = server_list
        self.connect('row_activated', self.server_select)
        def sort_function(row1, row2, data, notify_destroy):
            return row1.server.name.lower() > row2.server.name.lower()
        self.set_sort_func(sort_function, None, False)
        for server in server_list:
            self.add(PongoServerRow(server))
        self.show_all()
        zeroconf = Zeroconf()
        listener = PongoListener(self)
        self.updater = ServiceBrowser(zeroconf, "_pongo._tcp.local.", listener)

    def server_select(self, widget, row):
        print row.server;

    def remove_server(self, server):
        for row in self.get_children():
            if row.server == server:
                self.remove(row)
                break
        self.show_all()
        print [row.server for row in self.get_children()]

    def add_server(self, server):
        for row in self.get_children():
            if row.server == server:
                return
        self.add(PongoServerRow(server))
        self.show_all()
        print [row.server for row in self.get_children()]

    def shutdown(self):
        self.updater.cancel()
        self.updater = None
