#!/usr/bin/env python

import os
import pygtk
pygtk.require('2.0')
import gtk
import gobject

from gmusicapi import Mobileclient
from music_player import MusicPlayer
from widget import (SourcePane, ArtistPane, AlbumPane, SongPane,
                    get_player_control_toolbar, MainWindow, Login,
                    SongListStore)

api = Mobileclient()

gobject.threads_init()
from lastfm import AudioScrobbler

class Player(object):

    def __init__(self):
        self.window = MainWindow(gtk.WINDOW_TOPLEVEL)
        path = os.path.expanduser("~/.config/google_music_player")
        if not os.path.exists(path):
            message = Login(parent=self.window)
            message.run()
        path = os.path.expanduser("~/.config/google_music_player")
        while True:
            with open(path, "r") as fd:
                auth = fd.readlines()
                login, password = auth[:2]
                logged = api.login(
                    login.strip(),
                    password.strip(),
                    Mobileclient.FROM_MAC_ADDRESS)
                if logged:
                    last_fm = None
                    if len(auth) > 2:
                        try:
                            last_fm = AudioScrobbler()
                            last_fm.login(*auth[2:])
                        except Exception as e:
                            print e
                    else:
                        print "No Last"
                    break
                else:
                    message = Login(parent=self.window)
                    message.run()

        self.t = None # The music thread
        # Create a new window

        self.window.connect("delete_event", self.delete_event)

        # create the liststores (artist, album, songs)
        self.create_stores()
        self.refresh()
        self.create_base_panes()
        self.create_autocomplete()
        self.create_label_image()
        self.create_main_ui()
        self.create_right_click_menu()
        self.source_pane.connect("row-activated", self.expand)
        self.treeview.connect("row-activated", self.on_clicked)
        self.treeview.connect('button-press-event' , self.on_right_click)
        self.album_pane.get_selection().connect("changed", self.filter_album)
        self.artist_pane.get_selection().connect("changed", self.filter_artist)

        self.t = MusicPlayer(api, self, self.treeview, lastfm=last_fm)

    def create_base_panes(self):
        self.source_pane = SourcePane(self.source_store)
        self.source_scrolled_window = gtk.ScrolledWindow()
        self.source_scrolled_window.set_policy(
            gtk.POLICY_NEVER,
            gtk.POLICY_ALWAYS)
        self.source_scrolled_window.add(self.source_pane)


        self.artist_pane = ArtistPane(self.artist_store)
        self.artist_scrolled_window = gtk.ScrolledWindow()
        self.artist_scrolled_window.add(self.artist_pane)

        self.album_pane = AlbumPane(self.album_store)
        self.album_scrolled_window = gtk.ScrolledWindow()

        self.album_scrolled_window.add(self.album_pane)

        self.treeview = SongPane(self.liststore)
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.add(self.treeview)

    def create_right_click_menu(self):
        self.right_menu = gtk.Menu()
        like = gtk.MenuItem("Love")
        dislike = gtk.MenuItem("Dislike")
        clear = gtk.MenuItem("Clear rating")
        self.right_menu.append(like)
        self.right_menu.append(dislike)
        self.right_menu.append(clear)
        like.connect("activate", self.on_like, "like")
        dislike.connect("activate", self.on_like, "dislike")
        clear.connect("activate", self.on_like, "clear")
        like.show()
        dislike.show()
        clear.show()

    def create_autocomplete(self):
        self.completion_store = gtk.ListStore(str, str, str)
        completion = gtk.EntryCompletion()
        completion.set_model(self.completion_store)
        completion.set_text_column(0)
        self.search = gtk.Entry()
        self.search.set_completion(completion)
        self.search.connect("key-press-event", self.autocomplete)
        self.search.connect("activate", self.get_selection)

    def create_label_image(self):
        self.song_label = gtk.Label("")
        self.album_pic = gtk.Image()

    def create_main_ui(self):
        self.box = gtk.VBox()
        self.menubox = gtk.HBox()
        self.filters_box = gtk.HBox()
        self.main_box = gtk.HBox()
        self.right_box = gtk.VBox()

        # create the top menu bar
        self.menubox.pack_start(get_player_control_toolbar(self))
        self.menubox.pack_start(self.song_label)
        self.menubox.pack_end(self.search)

        # create the filter box
        self.filters_box.pack_start(self.artist_scrolled_window)
        self.filters_box.pack_start(self.album_scrolled_window)

        # create the right box
        self.right_box.pack_start(self.source_scrolled_window)
        self.right_box.pack_start(self.album_pic, expand=False)

        # create the vbox to hold filters and songs
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.filters_box)
        self.vbox.pack_start(self.scrolled_window)

        # add the rigth box to the main box
        self.main_box.pack_start(self.right_box, expand=False)
        # add the filters and songs to the main box
        self.main_box.pack_start(self.vbox)

        # add the menu to the window
        self.box.pack_start(self.menubox, expand=False)
        # add main box to the window
        self.box.add(self.main_box)

        self.window.add(self.box)
        self.window.show_all()

    def get_selection(self, widget, *args):
        text = widget.get_text()
        obj_type = None
        tracks = None
        for row in self.completion_store:
            if row[0] == text:
                obj_id, obj_type = row[1], row[2]
                break
        if obj_type == "artist":
            tracks = api.get_artist_info(
                obj_id, max_top_tracks=20)['topTracks']
        elif obj_type == "album":
            tracks = api.get_album_info(
                obj_id
            )['tracks']
        if tracks:
            for entry in tracks:
                entry["id"] = entry["storeId"]
            self.refresh(tracks)

    def autocomplete(self, widget, key):
        string = u"{}{}".format(self.search.get_text(), key.string)
        results = api.search(string, max_results=10)
        self.completion_store.clear()
        if results.get('artist_hits'):
            for artist in results.get('artist_hits'):

                self.completion_store.append([artist["artist"]["name"],
                                             artist["artist"]["artistId"],
                                              "artist"])
        if results.get('album_hits'):
            for album in results.get('album_hits'):

                self.completion_store.append([album["album"]["name"],
                                              album["album"]["albumId"],
                                              "album"])
        # print results.get('playlist_hits')
        # print results.get('song_hits')[0]

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def create_stores(self):
        self.liststore = SongListStore(str, str, str, str, str, str, str)
        self.album_store = gtk.ListStore(str)
        self.artist_store = gtk.ListStore(str)
        self.source_store = gtk.TreeStore(str)
        for elem in ["library", "playlists", "radios"]:
            self.source_store.append(None, [elem])

    def filter_songs(self, filter_key=None, filter_term=None):
        for song in self.songs:
            if not filter_key or song[filter_key] == filter_term:
                rating = song.get('rating')
                if rating == '5':
                    rating = '+1'
                elif rating == '1':
                    rating = '-1'
                else:
                    rating = None
                self.liststore.append(
                    [song["artist"],
                     song['album'],
                     song["title"],
                     song['id'],
                     song['albumArtRef'][0]['url'],
                     song["storeId"],
                     rating])

    def refresh(self, songs=None):
        if songs is None:
            self.songs = api.get_all_songs()

        else:
            self.songs = songs
        for store in [self.liststore, self.album_store, self.artist_store]:
            store.clear()
        for album in sorted(set([song['album'] for song in self.songs])):
            self.album_store.append([album])

        for artist in sorted(set([song['artist'] for song in self.songs])):
            self.artist_store.append([artist])
        self.songs = sorted(self.songs, key=lambda k: k['title'])
        self.filter_songs()


    def filter_album(self, selection):
        model, index = selection.get_selected_rows()
        if len(index) == 0:
            return
        index = index[0][0]
        album = self.album_store[index][0]
        self.liststore.clear()
        self.filter_songs('album', album)

    def filter_artist(self, selection):
        model, index = selection.get_selected_rows()
        index = index[0][0]
        artist = self.artist_store[index][0]
        self.liststore.clear()
        album_songs = []
        self.filter_songs('artist', artist)
        for song in self.songs:
            if song['artist'] == artist:
                album_songs.append(song['album'])

        self.album_store.clear()
        for album in set(album_songs):
            self.album_store.append([album])

    def on_clicked(self, widget, index, item):
        index = index[0]
        self.play()

    def on_right_click(self, widget, event):
        if event.button == 3:
            self.right_menu.popup(None, None, None, event.button, event.time)

    def on_like(self, widget, event):

        selection = self.treeview.get_selection()
        index = selection.get_selected_rows()[1][0][0]
        self.liststore.set_index(index)
        song = api.get_track_info(
            unicode(self.liststore[self.liststore.get_index()][5])
        )
        rating = ''
        if event == 'like':
            song['rating'], rating = '5', '+1'
        elif event == 'dislike':
            # dislike
            song['rating'], rating = '1', '-1'
        elif event == "clear":
            song['rating'], rating = '0', None
        api.change_song_metadata(song)
        self.liststore[index][6] = rating # update the ui

    def play(self):
        selection = self.treeview.get_selection()
        try:
            index = selection.get_selected_rows()[1][0][0]
        except IndexError:
            index = 0
        self.liststore.set_index(index)
        self.t.play()

    def get_index(self):
        return self.liststore.get_index()

    def set_index(self, index):
        return self.liststore.set_index(index)

    def previous(self):
        if self.get_index() > 0:
            self.set_index(self.get_index() - 1)
            self.t.play()

    def next(self):
        if self.get_index() +1 < self.liststore:
            self.set_index(self.get_index() + 1)
            self.t.play()


    def pause(self):
        if self.t:
            self.t.p.pause()

    def expand(self, widget, index, item):
        index = index
        it = self.source_store.get_iter(index)
        menu = self.source_store.get(it, 0)
        if len(index) == 1:
            if menu[0] == "playlists":
                self.playlists = api.get_all_user_playlist_contents()
                self.playlists = sorted(self.playlists, key=lambda k: k['name'])
                for playlist in self.playlists:
                    self.source_store.append(
                        self.source_store.get_iter(1),
                        [playlist["name"]])
            if menu[0]== "radios":
                self.radios = api.get_all_stations()
                self.radios = sorted(self.radios, key=lambda k: k['name'])
                for radio in self.radios:
                    self.source_store.append(
                        self.source_store.get_iter(2),
                        [radio["name"]])
        else:
            source_type = self.source_store.get_iter(index[0])
            if self.source_store.get(source_type, 0)[0] == "playlists":
                playlist = (
                    item for item in self.playlists
                    if item["name"] == menu[0]
                ).next()
                for entry in playlist['tracks']:
                    try:
                        entry["track"]["id"] = entry["trackId"]
                    except KeyError:
                        pass
                tracks = []
                for entry in playlist['tracks']:
                    if entry.get("track"):
                        tracks.append(entry['track'])
                self.refresh(tracks)
            elif self.source_store.get(source_type, 0)[0] == "radios":
                radio = (
                    item for item in self.radios
                    if item["name"] == menu[0]
                ).next()
                tracks = []
                for track in api.get_station_tracks(radio['id']):
                    track['id'] = track['nid']
                    tracks.append(track)
                self.refresh(tracks)
def main():
    gtk.main()

if __name__ == "__main__":

    player = Player()
    main()
