#!/usr/bin/env python
import os
import pygtk
pygtk.require('2.0')
import gtk
import gobject

from gmusicapi import Mobileclient
from music_player import MusicPlayer
from widget import (SourcePane, ArtistPane, AlbumPane, SongPane,
                    get_player_control_toolbar, MainWindow, Login)

api = Mobileclient()

gobject.threads_init()


class Player:

    def __init__(self):
        self.window = MainWindow(gtk.WINDOW_TOPLEVEL)
        path = os.path.expanduser("~/.config/google_music_player")
        if not os.path.exists(path):
            message = Login(parent=self.window)
            message.run()
        path = os.path.expanduser("~/.config/google_music_player")
        while True:
            with open(path, "r") as fd:
                login, password = fd.readlines()
                logged = api.login(
                    login.strip(),
                    password.strip(),
                    Mobileclient.FROM_MAC_ADDRESS)
                if logged:
                    break
                else:
                    message = Login(parent=self.window)
                    message.run()

        self.t = None # The music thread
        # Create a new window

        self.window.connect("delete_event", self.delete_event)

        # create the liststores (artist, album, songs)
        self.make_stores()
        self.refresh()
        # create the TreeView using liststore

        self.source_pane = SourcePane(self.source_store)
        self.source_scrolled_window = gtk.ScrolledWindow()

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

        self.main_hbox = gtk.HBox()
        self.hbox = gtk.HBox()
        self.hbox.add(self.source_scrolled_window)
        self.hbox.add(self.artist_scrolled_window)
        self.hbox.add(self.album_scrolled_window)

        self.menu_hbox = gtk.HBox()
        self.song_label = gtk.Label("")

        self.completion_store = gtk.ListStore(str, str, str)
        completion = gtk.EntryCompletion()
        completion.set_model(self.completion_store)
        completion.set_text_column(0)
        self.search = gtk.Entry()
        self.search.set_completion(completion)
        self.search.connect("key-press-event", self.autocomplete)
        self.search.connect("activate", self.get_selection)
        self.album_pic = gtk.Image()
        self.menu_hbox.pack_start(self.album_pic)
        self.menu_hbox.pack_start(get_player_control_toolbar(self))
        self.menu_hbox.pack_start(self.song_label)
        self.menu_hbox.pack_start(self.search)

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menu_hbox, expand=False)
        self.vbox.add(self.hbox)

        self.vbox.add(self.scrolled_window)

        self.window.add(self.vbox)

        self.window.show_all()

        self.source_pane.connect("row-activated", self.expand)
        self.treeview.connect("row-activated", self.on_clicked)
        self.album_pane.get_selection().connect("changed", self.filter_album)
        self.artist_pane.get_selection().connect("changed", self.filter_artist)

    def get_selection(self, widget, *args):
        text = widget.get_text()
        obj_type = None
        tracks = None
        for row in self.completion_store:
            if row[0] == text:
                name, obj_id, obj_type = row[0], row[1], row[2]
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
        results = api.search_all_access(string, max_results=10)
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
        if self.t:
            self.t.join()
        gtk.main_quit()
        return False

    def make_stores(self):
        self.liststore = gtk.ListStore(str, str, str, str, str)
        self.album_store = gtk.ListStore(str)
        self.artist_store = gtk.ListStore(str)
        self.source_store = gtk.TreeStore(str)
        for elem in ["library", "playlists", "radios"]:
            self.source_store.append(None, [elem])

    def refresh(self, songs=None):
        if songs is None:
            self.songs = api.get_all_songs()
        else:
            self.songs = songs
        for store in [self.liststore, self.album_store, self.artist_store]:
            store.clear()
        for album in set([song['album'] for song in self.songs]):
            self.album_store.append([album])

        for artist in set([song['artist'] for song in self.songs]):
            self.artist_store.append([artist])

        for song in self.songs:
            self.liststore.append(
                [song["artist"],
                 song['album'],
                 song["title"],
                 song['id'],
                 song['albumArtRef'][0]['url']])


    def filter_album(self, selection):
        model, index = selection.get_selected_rows()
        index = index[0][0]
        album = self.album_store[index][0]
        self.liststore.clear()
        for song in self.songs:
            if song['album'] == album:
                self.liststore.append(
                    [song["artist"],
                     song['album'],
                     song["title"],
                     song['id'],
                     song['albumArtRef'][0]['url']])

    def filter_artist(self, selection):
        model, index = selection.get_selected_rows()
        index = index[0][0]
        artist = self.artist_store[index][0]
        self.liststore.clear()
        album_songs = []
        for song in self.songs:
            if song['artist'] == artist:
                album_songs.append(song['album'])
                self.liststore.append(
                    [song["artist"],
                     song['album'],
                     song["title"],
                     song['id'],
                     song['albumArtRef'][0]['url']])

        self.album_store.clear()
        for album in set(album_songs):
            self.album_store.append([album])

    def on_clicked(self, widget, index, item):
        index = index[0]
        self.play(index= index)

    def play(self, index=None):
        if self.t:
            self.t.join()
        selection = self.treeview.get_selection()
        try:
            index = selection.get_selected_rows()[1][0][0]
        except IndexError:
            index = 0
        self.t = MusicPlayer(api, self, index, self.treeview)
        self.t.start()

    def pause(self):
        if self.t:
            self.t.p.pause()

    def stop(self):
        if self.t:
            self.t.p.stop()
            self.t.join()

    def expand(self, widget, index, item):
        index = index
        it = self.source_store.get_iter(index)
        menu = self.source_store.get(it, 0)
        if len(index) == 1:
            if menu[0] == "playlists":
                self.playlists = api.get_all_user_playlist_contents()
                for playlist in self.playlists:
                    self.source_store.append(
                        self.source_store.get_iter(1),
                        [playlist["name"]])
            if menu[0]== "radios":
                self.radios = api.get_all_stations()
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
