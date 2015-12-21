import threading
import time
import vlc
import gtk
import urllib2
from gmusicapi.utils import utils
from uuid import getnode as getmac

mac_int = getmac()
if (mac_int >> 40) % 2:
    raise OSError("a valid MAC could not be determined."
                  " Provide an android_id (and be"
                  " sure to provide the same one on future runs).")

android_id = utils.create_mac_string(mac_int)
android_id = android_id.replace(':', '')

class MusicPlayer(threading.Thread):

    def __init__(self, api, win, index, tree):
        super(MusicPlayer, self).__init__()
        self.win = win
        self.store = win.liststore
        self.index = index
        self.tree = tree
        self.stoprequest = threading.Event()
        self.api = api

    def join(self, timeout=None):
        self.stoprequest.set()
        self.p.stop()
        super(MusicPlayer, self).join(timeout)

    def play(self):

        try:
            artist = self.store[self.index][0]
            album = self.store[self.index][1]
            song = self.store[self.index][2]
            text = "{}-{}-{}".format(
                    song,
                    album,
                    artist)
            if len(text) > 50:
                text = text[:50] + '...'
            self.win.song_label.set_text(
                text
                )
            song = self.api.get_stream_url(
                self.store[self.index][3],
                device_id=android_id)
            self.p=vlc.MediaPlayer(song)
            self.p.play()
            response=urllib2.urlopen(self.store[self.index][4])
            loader=gtk.gdk.PixbufLoader()
            loader.set_size(50,50)
            loader.write(response.read())
            loader.close()
            self.win.album_pic.set_from_pixbuf(loader.get_pixbuf())
            self.watch(self.index)
        except IndexError:
            return


    def watch(self, index):
        while True:
            state = self.p.get_state()

            if state == vlc.State.Ended:
                self.api.increment_song_playcount(self.store[self.index][-1])
                self.index += 1
                self.play()
            elif state == vlc.State.Stopped:
                break
            else:
                time.sleep(1)

    def run(self):
        self.play()
