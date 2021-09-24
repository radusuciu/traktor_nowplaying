from collections import deque
from typing import List
import http.server
import html
import socketserver
import pathlib
import io
import os

from .options import PORT, QUIET, OUTPUT_FORMAT, APPEND, MAX_TRACKS
from .ogg import parse_comment, parse_pages
from .bottle import SimpleTemplate, TemplateError


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
    def __init__(self, quiet=QUIET, output_format=OUTPUT_FORMAT, outfile=None, template=None, append=APPEND, max_tracks=MAX_TRACKS):
        self.quiet = quiet
        self.outfile = outfile
        self.append = append

        self.max_tracks = max_tracks if append else 1
        self.tracks = deque(maxlen=self.max_tracks)

        try:
            self.output_format = SimpleTemplate(output_format)
        except TemplateError:
            print('Error encountered while trying to parse output format.')
            self.output_format = SimpleTemplate(OUTPUT_FORMAT)

        self.template = None
    
        if template is not None:
            try:
                self.template = SimpleTemplate(template)
            except TemplateError:
                print('Error encountered while trying to parse template.')

        if self.outfile:
            try:
                self._create_outfile()
            except:
                print(f'Error encountered while trying to write to {self.outfile}.')

    def update(self, data: List[tuple]):
        info = dict(data)

        if not ('artist' in info or 'title' in info):
            return

        self.tracks.append(info)

        if not self.quiet:
            self._to_stdout()
        if self.outfile:
            self._to_file()

    def _get_track_string(self, info):
        return html.unescape(self.output_format.render(
            artist=info.get('artist', ''),
            title=info.get('title', '')
        ))

    def _to_stdout(self):
        track_string = self._get_track_string(self.tracks[-1])
        if track_string:
            print(track_string)

    def _create_outfile(self):
        outpath = pathlib.Path(self.outfile)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        outpath.touch(exist_ok=True)

        if not outpath.is_file():
            print(f'{self.outfile} is a directory!')
            raise IsADirectoryError

    def _to_file(self):
        if self.template:
            tracklist = self.template.render(tracks=self.tracks)
        else:
            tracklist = os.linesep.join(self._get_track_string(t) for t in self.tracks)

        with open(self.outfile, 'w', encoding='utf-8') as f:
            f.write(tracklist)


class Listener():
    """Listens to Traktor broadcast, given a port."""

    def __init__(self, port=PORT, quiet=QUIET, output_format=OUTPUT_FORMAT, outfile=None, template=None, append=APPEND, max_tracks=MAX_TRACKS, custom_callback=None):
        self.port = port
        self.quiet = quiet
        self.output_format = output_format
        self.outfile = outfile
        self.template = template
        self.append = append
        self.max_tracks = max_tracks
        self.custom_callback = custom_callback

    def start(self):
        """Start listening to Traktor broadcast."""

        callbacks = []

        if self.outfile is not None or not self.quiet:
            writer = TrackWriter(
                quiet=self.quiet,
                output_format=self.output_format,
                outfile=self.outfile,
                template=self.template,
                append=self.append,
                max_tracks=self.max_tracks
            )
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
