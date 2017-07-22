Script that endlessly distributes the newest videos from a YouTube user/channel
to multiple Chromecasts.

## Installation:

On Debian boxes:


```
sudo apt-get update
sudo apt-get install python3-dev python3-pip git
sudo pip3 install PyChromecast youtube-dl
git clone https://github.com/theychx/multicast
```

## Usage:

```
python3 multicast.py [<chromecast> [<chromecast> ...]] <channel/user_url>
```

If no list of chromecasts is given, then all chromecasts on the network will be used.
