import urllib
import urllib2
import time
from datetime import datetime
from time import mktime
from md5 import md5


PROTOCOL_VERSION = '1.2'
login_url = "http://post.audioscrobbler.com/"
class AudioScrobbler(object):

    def __init__(self):
        self.cache = []

    def login(self, login, password):
        """
        Log to audioscrobbler services
        """
        tstamp = int(mktime(datetime.now().timetuple()))
        password = md5(password).hexdigest()
        token = md5( "%s%d" % (password, int(tstamp))).hexdigest()
        values = {
            'hs': 'true',
            'p' : PROTOCOL_VERSION,
            'c': 'tst',
            'v': '1.0',
            'u': login,
            't': tstamp,
            'a': token
        }
        data = urllib.urlencode(values)
        req = urllib2.Request("%s?%s" % (login_url, data) )
        response = urllib2.urlopen(req)
        result = [line.strip() for line in response.readlines()]
        if result[0] == "OK":
            self.session = result[1]
            self.now_url = result[2]
            self.post_url = result[3]

    def now_playing(self, artist, album, track, *args):
        """
        add a song to a now playing
        """
        values = {'s': self.session,
                  'a': unicode(artist).encode('utf-8'),
                  't': unicode(track).encode('utf-8'),
                  'b': unicode(album).encode('utf-8'),
                  'l': '',
                  'n': '',
                  'm': ''}

        data = urllib.urlencode(values)
        req = urllib2.Request(self.now_url, data)
        response = urllib2.urlopen(req)
        result = [line.strip() for line in response.readlines()]
        if result[0] == "OK":
            self.now_playing_cache = [artist, album, track]
            return True

    def submit(self, artist, album, track, rating="",
               length="", trackno="", mbid=""):
        """
        submit a song to a cache
        """
        timestamp = time.time()

        values = { 'a': unicode(artist).encode('utf-8'),
                   't': unicode(track).encode('utf-8'),
                   'i': timestamp,
                   'o': "U",
                   'r': rating,
                   'l': length,
                   'b': unicode(album).encode('utf-8'),
                   'n': trackno,
                   'm': mbid
               }
        self.cache.append(values)
        if len(self.cache) > 4:
            self.flush()
    def flush(self):
        """
        flush the cache. post all cached songs to lastfm
        """
        values = {}
        for i, item in enumerate(self.cache):
            for key in item:
                values[key + "[%d]" % i] = item[key]
        values['s'] = self.session
        data = urllib.urlencode(values)
        req = urllib2.Request(self.post_url, data)
        response = urllib2.urlopen(req)
        result = [line.strip() for line in response.readlines()]
        if result[0] == "OK":
            return True
