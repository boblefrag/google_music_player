import vlc
import gtk
import urllib2
from gmusicapi.utils import utils
from uuid import getnode as getmac
from vlc import callbackmethod
mac_int = getmac()
if (mac_int >> 40) % 2:
    raise OSError("a valid MAC could not be determined."
                  " Provide an android_id (and be"
                  " sure to provide the same one on future runs).")

android_id = utils.create_mac_string(mac_int)
android_id = android_id.replace(':', '')

@callbackmethod
def SongFinished(self, player):
    if player.lastfm:
        player.lastfm.submit(*player.lastfm.now_playing_cache)
    player.api.increment_song_playcount(
        player.win.liststore[player.win.get_index()][2])
    player.win.set_index(player.win.get_index() + 1)
    player.play()


class MusicPlayer(object):

    def __init__(self, api, win, tree, lastfm=None):

        super(MusicPlayer, self).__init__()
        self.win = win
        self.store = win.liststore
        self.tree = tree
        self.api = api
        self.lastfm = lastfm
        self.p = vlc.MediaPlayer()

    def make_label(self, data):
        artist = data[0]
        album = data[1]
        song = data[2]
        text = "{}-{}-{}".format(
            song,
            album,
            artist)
        if len(text) > 50:
            text = text[:50] + '...'
        self.win.song_label.set_text(
            text
                )
    def _play(self, data):
        if self.p.get_state() in [vlc.State.Playing, vlc.State.Paused] :
            self.p.stop()
        song = self.api.get_stream_url(
            data[3],
            device_id=android_id)
        self.p = vlc.MediaPlayer(song)
        self.p.play()
        self.p.event = self.p.event_manager()
        self.p.event.event_attach(
            vlc.EventType.MediaPlayerEndReached, SongFinished, self)

    def play(self):
        """
        data is : [artist, album, song, uuid, cover]
        """
        selection = self.tree.get_selection()
        selection.select_path(self.win.get_index())
        try:
            data = self.win.liststore[self.win.get_index()]
        except IndexError:
            return
        if self.lastfm:
            self.lastfm.now_playing(*data)
        self._play(data)
        self.make_label(data)
        self.create_thumb()

    def create_thumb(self):
        response=urllib2.urlopen(self.store[self.win.get_index()][4])
        loader=gtk.gdk.PixbufLoader()
        loader.set_size(200,200)
        loader.write(response.read())
        loader.close()
        self.win.album_pic.set_from_pixbuf(loader.get_pixbuf())
