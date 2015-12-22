import gtk
import os
from gettext import gettext as _

class SongListStore(gtk.ListStore):

    def __init__(self, *args, **kwargs):
        super(SongListStore, self).__init__(*args, **kwargs)
        self.index = 0

    def clear(self, *args, **kwargs):
        super(SongListStore, self).clear(*args, **kwargs)
        self.index = 0

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index
        return self.index

def get_player_control_toolbar(win):
    """Return a player control toolbar
    """
    tb = gtk.Toolbar()
    tb.set_style(gtk.TOOLBAR_ICONS)
    for text, tooltip, stock, callback in (

            (_("Previous"), _("Previous"),
             gtk.STOCK_MEDIA_PREVIOUS, lambda b: win.previous()),

            (_("Play"), _("Play"),
             gtk.STOCK_MEDIA_PLAY,lambda b: win.play()),

            (_("Pause"), _("Pause"),
             gtk.STOCK_MEDIA_PAUSE, lambda b: win.pause()),

            (_("Next"), _("Next"),
             gtk.STOCK_MEDIA_NEXT, lambda b: win.next()),

            (_("Refresh"),_("Refresh"),
             gtk.STOCK_REFRESH, lambda b: win.refresh())

            ):
        b=gtk.ToolButton(stock)
        b.set_tooltip_text(tooltip)
        b.connect("clicked", callback)
        tb.insert(b, -1)
        tb.show_all()
    return tb


class SourcePane(gtk.TreeView):

    def __init__(self, *args, **kwargs):
        super(SourcePane, self).__init__(*args, **kwargs)
        self.tvcolumn = gtk.TreeViewColumn('Source')
        self.set_search_column(0)
        self.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, False)
        self.tvcolumn.set_attributes(self.cell, text=0)
        self.tvcolumn.set_clickable(True)
        self.tvcolumn.set_sort_column_id(0)
        self.set_reorderable(False)


class ArtistPane(gtk.TreeView):

    def __init__(self, *args, **kwargs):
        super(ArtistPane, self).__init__(*args, **kwargs)
        self.tvcolumn = gtk.TreeViewColumn('Artist')
        self.set_search_column(0)
        self.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, False)
        self.tvcolumn.set_attributes(self.cell, text=0)
        self.tvcolumn.set_clickable(True)
        self.tvcolumn.set_sort_column_id(0)
        self.set_reorderable(True)



class AlbumPane(gtk.TreeView):

    def __init__(self, *args, **kwargs):
        super(AlbumPane, self).__init__(*args, **kwargs)
        self.tvcolumn = gtk.TreeViewColumn('Album')
        self.set_search_column(0)
        self.tvcolumn.set_clickable(True)
        self.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, False)
        self.tvcolumn.set_attributes(self.cell, text=0)
        self.set_reorderable(True)
        self.tvcolumn.set_sort_column_id(0)

class SongPane(gtk.TreeView):

    def __init__(self, *args, **kwargs):
        super(SongPane, self).__init__(*args, **kwargs)
        self.tvcolumn = gtk.TreeViewColumn('Title')
        self.tvcolumn1 = gtk.TreeViewColumn('Album')
        self.tvcolumn2 = gtk.TreeViewColumn('Artist')
        self.set_search_column(0)

        self.tvcolumn.set_sort_column_id(0)
        self.tvcolumn1.set_sort_column_id(0)
        self.tvcolumn.set_clickable(True)

        self.append_column(self.tvcolumn)
        self.append_column(self.tvcolumn1)
        self.append_column(self.tvcolumn2)
        self.cell = gtk.CellRendererText()
        self.cell1 = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, False)
        self.tvcolumn.set_attributes(self.cell, text=2)
        self.tvcolumn1.pack_start(self.cell1, False)
        self.tvcolumn1.set_attributes(self.cell1, text=1)
        self.tvcolumn2.pack_start(self.cell2, False)
        self.tvcolumn2.set_attributes(self.cell2, text=0)
        self.set_reorderable(True)


class LibraryPane(gtk.TreeView):

    def __init__(self, *args, **kwargs):
        super(LibraryPane, self).__init__(*args, **kwargs)



class MainWindow(gtk.Window):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.set_title("Google Music Player")


class Login(gtk.Dialog):

    def __init__(self, *args, **kwargs):
        super(Login, self).__init__(*args, **kwargs)
        self.label = gtk.Label("set your mail and password in order to connect")
        self.mail = gtk.Entry()
        self.password = gtk.Entry()
        self.password.set_visibility(False)
        self.message = gtk.Dialog()
        self.button = gtk.Button(stock=gtk.STOCK_APPLY)
        self.button.connect("clicked", self.clicked)
        self.vbox.pack_start(self.label)
        self.vbox.pack_start(self.mail)
        self.vbox.pack_start(self.password)
        self.action_area.pack_start(self.button)
        self.show_all()

    def clicked(self, widget):
        user_email = self.mail.get_text()
        user_password = self.password.get_text()
        path = os.path.expanduser("~/.config/google_music_player")
        with open(path, "w") as fd:
            fd.write("{}\n".format(user_email))
            fd.write("{}\n".format(user_password))
        self.destroy()
