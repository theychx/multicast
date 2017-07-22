#! /usr/bin/env python3

import sys
import threading

import pychromecast
import youtube_dl


# Put the names of your chromcasts into this list.
#CHROMECAST_NAMES = ['chromecast1', 'chromecast2', 'chromecast3', 'chromecast4']
CHROMECAST_NAMES = ['audio', 'video']
# Insert YouTube channel/user url here.
CHANNEL_URL = 'https://www.youtube.com/user/CrazyFrogVEVO/videos'


class MulticastError(Exception):
    pass


class MulticastPlaylistError(MulticastError):
    pass


class MulticastNoDevicesError(MulticastError):
    pass


class MulticastCastError(MulticastError):
    pass


class Playlist:
    def __init__(self, channel_url):
        self._ydl = youtube_dl.YoutubeDL({'quiet': True, 'no_warnings': True})
        self.next_entry = None
        self._url_cache = dict()
        try:
            chaninfo = self._ydl.extract_info(channel_url, process=False)
            if not (chaninfo['extractor'] == 'youtube:channel'
                    or chaninfo['extractor'] == 'youtube:user'):
                raise ValueError
        except (youtube_dl.utils.DownloadError, ValueError):
            raise MulticastPlaylistError
        self._playlist_url = chaninfo['url']

    def update(self):
        preinfo = self._ydl.extract_info(self._playlist_url, process=False)
        self.next_entry = ((self._get_best_format(entry), entry['id'])
                           for entry in list(preinfo['entries']))

    def _get_best_format(self, preinfo):
        try:
            video_url = self._url_cache[preinfo['id']]
        except KeyError:
            info = self._ydl.process_ie_result(preinfo, download=False)
            format_selector = self._ydl.build_format_selector('best')
            try:
                best_format = list(format_selector(info))[0]
            except KeyError:
                best_format = info
            video_url = self._url_cache[preinfo['id']] = best_format['url']

        return video_url


class PlaybackHub:
    available = threading.Event()


class StatusListener:
    def __init__(self, runningapp):
        self._appid = 'CC1AD845'
        self.ready = threading.Event()
        self.active = threading.Event()

        if runningapp == self._appid:
            self.ready.set()

    def new_cast_status(self, status):
        if status.app_id == self._appid:
            self.ready.set()
        else:
            self.ready.clear()

    def new_media_status(self, status):
        if self.active.is_set():
            if status.player_state in ['UNKNOWN', 'IDLE']:
                self.active.clear()
                PlaybackHub.available.set()
        elif self.ready.is_set():
            if status.player_state in ['BUFFERING', 'PLAYING']:
                self.active.set()


class Caster:
    def __init__(self, ipadress):
        self.video_id = None
        self._cast = pychromecast.Chromecast(ipadress)
        self._cast.wait()
        self._listener = StatusListener(self._cast.app_id)
        self._cast.register_status_listener(self._listener)
        self._cast.media_controller.register_status_listener(self._listener)

    @property
    def name(self):
        return self._cast.name

    @property
    def is_active(self):
        return self._listener.active.is_set()

    def play(self, video_url, video_id):
        self.video_id = video_id
        self._cast.play_media(video_url, 'video/mp4')
        self._listener.ready.wait()
        self._listener.active.wait()

    def stop(self):
        self._cast.quit_app()


def main():
    devices = pychromecast.get_chromecasts()
    if not devices:
        raise MulticastNoDevicesError
    try:
        casts = [Caster(cc.host)
                 for cc in devices if cc.name in CHROMECAST_NAMES]
        if not casts:
            raise ValueError
    except (pychromecast.error.ChromecastConnectionError, ValueError):
        raise MulticastCastError

    for cast in casts:
        cast.stop()

    playlist = Playlist(CHANNEL_URL)

    print('Press Ctrl+C to stop all casting and terminate script.')

    while True:
        try:
            playlist.update()
            available_casts = [cc for cc in casts if not cc.is_active]
            playing_videos = [cc.video_id for cc in casts if cc.is_active]

            for cast in available_casts:
                video_url, video_id = next(entry for entry in playlist.next_entry
                                           if entry[1] not in playing_videos)
                print('Playing %s on "%s"' % (video_id, cast.name))
                cast.play(video_url, video_id)

            if all(cc.is_active for cc in casts):
                PlaybackHub.available.clear()
            PlaybackHub.available.wait()
        except KeyboardInterrupt:
            for cast in casts:
                cast.stop()
            break


if __name__ == '__main__':
    try:
        main()
    except MulticastPlaylistError:
        sys.exit('Error: Invalid YouTube channel/user url.')
    except MulticastNoDevicesError:
        sys.exit('Error: No Chromecast devices found.')
    except MulticastCastError:
        sys.exit('Error: Invalid Chromecast list.')
