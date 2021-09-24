[![PyPI pyversions](https://img.shields.io/pypi/pyversions/traktor-nowplaying.svg)](https://pypi.python.org/pypi/traktor-nowplaying/)
[![PyPI version fury.io](https://img.shields.io/pypi/v/traktor-nowplaying.svg)](https://pypi.python.org/pypi/traktor-nowplaying/)
[![GitHub release](https://img.shields.io/github/release/radusuciu/traktor_nowplaying.svg)](https://github.com/radusuciu/traktor_nowplaying/releases/)

# Traktor Now Playing

This project for Python 3 (tested on 3.6+) uses Traktor's broadcast functionality to extract metadata about the currently playing song. This is really a very thin wrapper around some [tinytag](https://github.com/devsnd/tinytag) methods that can be found in `ogg.py`, where the original license is also included. There are no dependencies. Tested with Traktor 3.3, but this will likely work with older versions as well.

The reason this exists is because it's rather difficult to get this information through other means. You can [use MIDI](https://github.com/Sonnenstrahl/traktor-now-playing) for this as well, but that requires that you add a fake controller.

Lastly, there are several other projects that do something similar such as [Traktor Metadata Listener](https://www.disconova.com/utu/traktor-metadata/) which is not open-source and likely will never be, and [traktor-now-playing](https://github.com/Sonnenstrahl/traktor-now-playing), which uses the MIDI approach mentioned above.

## Installation

The preferred installation method is via [pip](https://pip.pypa.io/en/stable/):

```bash
pip install traktor_nowplaying
```

There are also binary releases available for Windows, Linux, and MacOS. These are created using `pyInstaller` and GitHub actions and can be downloaded from [the project Releases page](https://github.com/radusuciu/traktor_nowplaying/releases).

## General use

In order for this program to work, you of course have to setup the broadcasting feature of Traktor - note that this completely hijacks that functinality, so while you can still record and broadcast through some other means (eg. using a splitter or other outputs on your controller/mixer, or [from the recording itself](https://radusuciu.com/posts/broadcasting-from-traktor-an-alternative-to-the-built-in-broadcasting-function/)), you cannot broadcast from Traktor itself.

You must configure Traktor to broadcast to `localhost` and the port specified with the `-p`, or `--port` option (defaults to `8000`), or the port that is passed to the constructor if you're using this as a library instead. For the format setting you can use anything, but I recommend choosing the lowest bitrate for the sample rate of your system, so most commonly the best choice is 44100 Hz, 64 Kbps.

Note that there is a delay between when you change a song in Traktor and when the change is picked up.

## Use from command line

If you run the program without specifying any options you'll be asked if you want to set the options interactively, or you can hit enter which uses all default options, which are to listen on port `8000`, and output the currently playing song to the console:
```bash
traktor_nowplaying
```

Listen on port `8000`, output to `nowplaying.txt` in the current directory and do not output to `stdout`:
```bash
traktor_nowplaying --port 8000 --outfile='nowplaying.txt' --quiet
```

The help text:
```
$ traktor_nowplaying --help
usage: traktor_nowplaying [-h] [-p PORT] [-q] [-f FORMAT] [-o OUTFILE]
                          [-t TEMPLATE] [-a] [-m MAX_TRACKS] [-i] [-v]

Use Traktor's broadcast functionality to extract metadata about the currently
playing song

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on for broadcasts from Traktor
  -q, --quiet           Suppress console output of currently playing song
  -f FORMAT, --format FORMAT
                        Custom format to use when outputting tracks
  -o OUTFILE, --outfile OUTFILE
                        Provide a file path to which the currently playing song
                        should be written
  -t TEMPLATE, --template TEMPLATE
                        Template file to use for output. Templating is
                        implemented using Bottle SimpleTemplate
                        (https://bottlepy.org/docs/0.12/stpl.html). See README
                        for more details on use. Note: the --format options is
                        ignored when using a custom template file. Take care
                        when using templates provided by others on the internet
                        as they can contain malicious code.
  -a, --append          If writing to file, appends newest track to end of file
                        instead of overwriting the file
  -m MAX_TRACKS, --max-tracks MAX_TRACKS
                        If appending to a file, the maximum number of tracks to
                        keep in file (by default there is no limit)
  -i, --interactive     Interactive mode allows for settings to be specified at
                        runtime. These override command line options.
  -v, --version         show program's version number and exit

Note that you must configure Traktor to broadcast to localhost and the port
specified with the -p, or --port option (defaults to 8000). For the format
setting you can use anything, but I recommend choosing the lowest bitrate for
the sample rate of your system, so most commonly the best choice is 44100 Hz,
64 Kbps.
```

To stop the process `Ctrl + C` should suffice.

## Using binary releases

If you've downloded a platform specific release from [the Releases page](https://github.com/radusuciu/traktor_nowplaying/releases), the use instructions are the same as described above for the command-line.

## Use as a library

`traktor_nowplaying` can also be used as a library. This can be useful if you'd like to leverage this rather simple functionality in other code.

```python
from traktor_nowplaying import Listener

listener = Listener(port=8000, quiet=True, outfile='nowplaying.txt')
listener.start()
```

For a more elaborate example with a custom callback, see this project: https://github.com/radusuciu/traktor_ice, and [this bit](https://github.com/radusuciu/traktor_ice/blob/b0873cb5e36dbcb87a260900f44a2f1768d5d5c9/traktor_ice/core.py#L60-L74) in particular.

## Customizing output

The output of `traktor_nowplaying` can be customized using the `--format` and `--template` options. Both of these functions make use of the [`SimpleTemplate` Engine](https://bottlepy.org/docs/0.12/stpl.html) included with [Bottle 0.12](https://bottlepy.org/docs/0.12/), so anything you can use with Bottle's templates, you can use here.

**Note**: Please take care when using format strings or templates provided by others on the internet. These can contain malicious code. I doubt this will be the case since this is such an obscure project and I can't imagine templates being complex enough to hide malware, but you never know.

### `--format`

This option allows for the specification of alternate ways to display tracks. By default, tracks are formatted using a simple template: `{{artist}} - {{title}}`. You can change the order: `{{title}} - {{artist}}`, only display the title `{{title}}`, or sprinkle in some HTML: `<p><strong>{{artist}}</strong> - {{title}}`.

### `--template`

While `--format` allows you to control the display of each individual track, `--template` allows you to specify a template file. This template file will be passed a `tracks` variable that contains a list of tracks to display. Each individual track is a Python `dict` with `artist` and `title` keys. Here's an example:

```html
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        % for track in tracks:
        <p><strong>{{track.get('artist', '')}}</strong> - {{track.get('title', '')}}</p>
        % end
    </body>
</html>
```

If you save the above as `template.html` you can use it like so: `traktor_nowplaying --template template.html --append`. Note that without setting `--append`, you will only have the latest track being output.

**Note**: Templates don't have to be HTML

**Note**: `--template` overrides `--format`.

## Development

Some notes, mostly for myself about developing traktor_nowplaying.

### Releasing

Binary releases are created using [pysinstaller](https://www.pyinstaller.org/) and the following command:

```bash
pyinstaller traktor_nowplaying/cli.py -n traktor_nowplaying --onefile --icon=assets/icon.ico
```

These are automatically handled by GitHub actions, which are triggered when a new tag is pushed.
