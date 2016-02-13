from gi.repository import Gtk
from gi.repository import Pango
import sys

columns = ["Pongo Name"]

pongos = [['Pongo One'], ['Pongo Two'], ['Pongo Three']]

class CellRendererButton(Gtk.CellRenderer):
    def __init__(self):
        Gtk.CellRenderer.__init__(self)

    def do_get_size(self, widget, cell_area):
        buttonHeight = cell_area.height
        buttonWidth = buttonHeight
        return (0, 0, buttonWidth, buttonHeight)

    def do_render(self, window, widget, background_area, cell_area, expose_area, flags):
        style = widget.get_style()
        x, y, buttonWidth, buttonHeight = self.get_size()
        style.paint_box(window,
                        widget.get_state(),
                        Gtk.SHADOW_ETCHED_OUT,
                        expose_area,
                        widget,
                        None,
                        0, 0, buttonWidth, buttonHeight)


class FindPongoWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        Gtk.Window.__init__(self, title="Pongo", application=app)
        self.set_default_size(250, 100)
        self.set_border_width(10)
        listmodel = Gtk.ListStore(str)
        # append the values in the model
        for i in range(len(pongos)):
            listmodel.append(pongos[i])

        # a treeview to see the data stored in the model
        view = Gtk.TreeView(model=listmodel)

        # for each column
        for i in range(len(columns)):
            cell = Gtk.CellRendererText()
            cell.props.weight_set = True
            cell.props.weight = Pango.Weight.BOLD
            col = Gtk.TreeViewColumn(columns[i], cell, text=i)
            view.append_column(col)
            view.set_headers_visible(False)

        # when a row is selected, it emits a signal
        view.get_selection().connect("changed", self.on_changed)

        # the label we use to show the selection
        self.label = Gtk.Label()
        self.label.set_text("")

        # a grid to attach the widgets
        grid = Gtk.Grid()
        grid.attach(view, 0, 0, 1, 1)
        grid.attach(self.label, 0, 1, 1, 1)

        # attach the grid to the window
        self.add(grid)

    def on_changed(self, selection):
        # get the model and the iterator that points at the data in the model
        (model, iter) = selection.get_selected()
        # set the label to a new value depending on the selection
        self.label.set_text("\n %s" %
                            (model[iter][0]))
        return True
