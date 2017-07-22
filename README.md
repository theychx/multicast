Script that endlessly distributes the newest videos from a YouTube user/channel
to multiple Chromecasts.

## Prerequisites:

```
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo pip3 install PyChromecast youtube-dl
```

## Usage:

```
python3 multicast.py [<chromecast> [<chromecast> ...]] <channel/user_url>
```

If no list of chromecasts is given, then all chromecasts on the network will be used.
