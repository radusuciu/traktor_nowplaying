"""
Contains a command-line interface implemented with argparse.
"""

from traktor_nowplaying.core import Listener
from traktor_nowplaying.options import PORT, QUIET
from traktor_nowplaying.version import __version__
import argparse

DESCRIPTION = 'Use Traktor\'s broadcast functionality to extract metadata about the currently playing song'
EPILOG = f'Note that you must configure Traktor to broadcast to localhost and the port specified with the -p, or --port option (defaults to {PORT}). For the format setting you can use anything, but I recommend choosing the lowest bitrate for the sample rate of your system, so most commonly the best choice is 44100 Hz, 64 Kbps.'

parser = argparse.ArgumentParser(
    description=DESCRIPTION,
    epilog=EPILOG
)

parser.add_argument('-p', '--port', default=PORT,
    type=int,
    help='Port to listen on for broadcasts from Traktor'    
)

parser.add_argument('-q', '--quiet', default=QUIET,
    action='store_true',
    help='Suppress console output of currently playing song'
)

parser.add_argument('-o', '--outfile', default=None,
    help='Provide a file path to which the currently playing song should be written',
)

parser.add_argument('-v', '--version',
    action='version',
    version='%(prog)s {version}'.format(version=__version__)
)

args = parser.parse_args()

def main():
    listener = Listener(port=args.port, quiet=args.quiet, outfile=args.outfile)
    listener.start()

if __name__ == '__main__':
    main()
