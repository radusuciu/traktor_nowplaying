"""
Contains a command-line interface implemented with argparse.
"""

from traktor_nowplaying.core import Listener
from traktor_nowplaying.options import PORT, QUIET, INTERACTIVE, APPEND, MAX_TRACKS
from traktor_nowplaying.version import __version__
import argparse
import signal
import sys


DESCRIPTION = 'Use Traktor\'s broadcast functionality to extract metadata about the currently playing song'
EPILOG = f'Note that you must configure Traktor to broadcast to localhost and the port specified with the -p, or --port option (defaults to {PORT}). For the format setting you can use anything, but I recommend choosing the lowest bitrate for the sample rate of your system, so most commonly the best choice is 44100 Hz, 64 Kbps.'
PROGRAM_NAME = 'traktor_nowplaying'

parser = argparse.ArgumentParser(
    description=DESCRIPTION,
    epilog=EPILOG,
    prog=PROGRAM_NAME,
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

parser.add_argument('-a', '--append', default=APPEND,
    action='store_true',
    help='If writing to file, appends newest track to end of file instead of overwriting the file'
)

parser.add_argument('-m', '--max-tracks', default=MAX_TRACKS,
    action='store',
    type=int,
    help='If appending to a file, the maximum number of tracks to keep in file (by default there is no limit)'
)

parser.add_argument('-i', '--interactive', default=INTERACTIVE,
    action='store_true',
    help='Interactive mode allows for settings to be specified at runtime. These override command line options.'
)

parser.add_argument('-v', '--version',
    action='version',
    version='%(prog)s {version}'.format(version=__version__)
)


def _exit(status=None):
    print('\n Exiting')
    sys.exit(status)

# capture Ctrl + C
signal.signal(signal.SIGINT, lambda signum, frame: _exit())

def _get_port_interactively():
    MIN_PORT = 1
    MAX_PORT = 65535

    port = None

    while True:
        try:
            port = input(f'Please specify port to listen on (press Enter to accept default: {PORT}): ').strip()

            # accepted default
            if port == '':
                break
            
            # attempt to convert to int
            port = int(port)

            # and make sure it is valid
            if port < MIN_PORT or port > MAX_PORT:
                raise ValueError
        except ValueError:
            print(f'Port needs to be an integer between {MIN_PORT}-{MAX_PORT}')
        except KeyboardInterrupt:
            _exit()

    return port

def interactive():
    print('Interactive mode is active. Press Enter to accept the default for each choice.')
    port = _get_port_interactively()
    # Ask for y/n but also strip extra space
    quiet = input(f'Quiet mode (suppresses console output)? (Y/[N], default N): ').lower().strip() or 'n'
    # and also accept "yes" or really yXX by truncating string
    quiet = (quiet[0] == 'y')
    outfile = input('Path of file to output current playing song to (no file output by default): ').strip()
    _args = []

    if port:
        _args.extend(['--port', port])
    if quiet:
        _args.extend(['--quiet'])
    if outfile:
        _args.extend(['--outfile', outfile])

        append = input('Append latest track to end of file? (Y/[N], default N): ').lower().strip() or 'n'
        # and also accept "yes" or really yXX by truncating string
        append = (append[0] == 'y')
        if append:
            _args.extend(['--append'])
        
            try:
                max_tracks = input('Number of tracks to keep in file (default no limit): ')
                if int(max_tracks) > 0:
                    _args.extend(['--max-tracks', max_tracks])
            except ValueError:
                pass

    print(f"{parser.prog} {' '.join(_args)}")

    return _args

def want_interactive():
    while True:
        answer = input(' '.join([
            'Type the letter i (then press Enter) to set options',
            'interactively or press h (then press Enter) for help, '
            'or just press Enter to continue with default options: '
        ])).lower().strip()

        if answer == 'h':
            parser.print_help()
            print('\n')
            continue

        return answer == 'i'

def main():
    args = parser.parse_args()
    # set arguments interactively if interactive flag is passed
    # or if the user passes no arguments and desires interactive mode
    if args.interactive or (len(sys.argv) == 1 and want_interactive()):
        args = parser.parse_args(interactive())

    listener = Listener(port=args.port, quiet=args.quiet, outfile=args.outfile, append=args.append, max_tracks=args.max_tracks)
    listener.start()

if __name__ == '__main__':
    main()
