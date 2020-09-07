from .options import PORT, QUIET, MAX_TRACKS, APPEND
from .ogg import parse_comment, parse_pages
import functools
import http.server
import socketserver
import pathlib
import types
import io
import os


def create_request_handler(callbacks):
    """Creates an HTTP request handler with a custom callback"""

    class TraktorHandler(http.server.BaseHTTPRequestHandler):
        """Simpler handler for Traktor requests."""

        def do_SOURCE(self):
            """
            Implement handler for SOURCE requests which Traktor and older
            icecast source cilents send data via a special SOURCE verb.
            """
            # we send response
            self.send_response(200)
            # and headers
            self.end_headers()

            # and now the streaming begins
            for packet in parse_pages(self.rfile):
                walker = io.BytesIO(packet)
                if packet[:7] == b"\x03vorbis":
                    walker.seek(7, os.SEEK_CUR)  # jump over header name
                    metadata = parse_comment(walker)

                    for callback in callbacks:
                        callback(metadata)

        def log_request(self, code='-', size='-'):
            """Do not log messages about HTTP requests."""
            pass

        def log_error(self, format, *args):
            """Do not log messages about HTTP requests."""
            pass

    return TraktorHandler


class TrackWriter:
    """Writes tracks to standard output and/or file."""
    def __init__(self, quiet=QUIET, outfile=None, append=APPEND, max_tracks=MAX_TRACKS):
        self.quiet = quiet
        self.outfile = outfile
        self.append = append
        self.max_tracks = max_tracks

        if self.outfile:
            try:
                self._create_outfile()
            except:
                print(f'Error encountered while trying to write to {self.outfile}.')

    def update(self, data):
        if not self.quiet:
            self._to_stdout(data)
        if self.outfile:
            self._to_file(data)

    def _get_track_string(self, data):
        info = dict(data)
        track_string = f'{info.get("artist", "")} - {info.get("title", "")}'
        return track_string if len(track_string) > 3 else ''

    def _to_stdout(self, data):
        track_string = self._get_track_string(data)
        if track_string:
            print(track_string)

    def _create_outfile(self):
        outpath = pathlib.Path(self.outfile)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        outpath.touch(exist_ok=True)

        if not outpath.is_file():
            print(f'{self.outfile} is a directory!')
            raise IsADirectoryError

    def _to_file(self, data):
        mode = 'a' if (self.append and self.max_tracks < 0)  else 'w'

        current_track_string = self._get_track_string(data)
        tracks_to_output = [current_track_string]

        if self.max_tracks > 1:
            with open(self.outfile, 'r') as f:
                existing_tracks = f.read().splitlines()

            tracks_to_output = [
                *existing_tracks[-(self.max_tracks - 1):],
                current_track_string
            ]

        with open(self.outfile, mode) as f:
            f.write('\n'.join(tracks_to_output))


class Listener():
    """Listens to Traktor broadcast, given a port."""

    def __init__(self, port=PORT, quiet=QUIET, outfile=None, append=APPEND, max_tracks=MAX_TRACKS, custom_callback=None):
        self.port = port
        self.quiet = quiet
        self.outfile = outfile
        self.append = append
        self.max_tracks = max_tracks
        self.custom_callback = custom_callback

    def start(self):
        """Start listening to Traktor broadcast."""

        callbacks = []

        if self.outfile is not None or not self.quiet:
            writer = TrackWriter(self.quiet, self.outfile, self.append, self.max_tracks)
            callbacks.append(writer.update)

        if not self.quiet:
            print(f'Listening on port {self.port}.')
            if self.outfile:
                print(f'Outputting to {self.outfile}')

        if self.custom_callback:
            callbacks.append(self.custom_callback)

        # create a request handler with appropriate callback
        handler = create_request_handler(callbacks=callbacks)

        with socketserver.TCPServer(('', self.port), handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
