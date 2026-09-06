from unittest import TestCase
import unittest
import tempfile
import os
import io
import struct
import socket
import time
import threading

from traktor_nowplaying.core import TrackWriter, Listener
from traktor_nowplaying.ogg import parse_comment


def build_comment_header(comments, vendor=b'test'):
    """Build the body of a Vorbis comment header (without the packet type/name)."""
    out = struct.pack('<I', len(vendor)) + vendor
    out += struct.pack('<I', len(comments))
    for comment in comments:
        out += struct.pack('<I', len(comment)) + comment
    return io.BytesIO(out)


class TestParseComment(TestCase):
    def test_unknown_fields_are_passed_through_lowercased(self):
        metadata = parse_comment(build_comment_header([
            b'ARTIST=Test Artist',
            b'TITLE=Test Title',
            b'BPM=128',
        ]))

        self.assertEqual(metadata, [
            ('artist', 'Test Artist'),
            ('title', 'Test Title'),
            ('bpm', '128'),
        ])

    def test_known_fields_keep_mapped_names(self):
        metadata = parse_comment(build_comment_header([
            b'DATE=2024',
            b'TRACKNUMBER=3',
        ]))

        self.assertEqual(metadata, [('year', '2024'), ('track', '3')])


class TestTrackWriter(TestCase):
    def test_file_output(self):
        writer = TrackWriter()

        writer.update({
            'title': 'Title',
            'artist': 'Artist'
        })
        writer.update({
            'title': '音楽',
            'artist': 'Artist'
        })


class TestFileWriter(TestCase):
    def test_multiline_template_windows(self):
        with tempfile.TemporaryDirectory() as d:
            test_file_path = os.path.join(d, 'test.txt')

            writer = TrackWriter(
                output_format='{{artist}}\r\n{{title}}',
                outfile=test_file_path,
                quiet=True,
                append=True
            )
            writer.update([('artist', 'foo'), ('title', 'bar')])

            with open(test_file_path) as f:
                self.assertEqual(len(f.readlines()), 2)

            writer.update([('artist', 'foo2'), ('title', 'bar2')])

            with open(test_file_path) as f:
                self.assertEqual(len(f.readlines()), 4)


class TestListener(TestCase):
    def setUp(self):
        self.test_ogg_file = 'test_single_track_1ms.ogg'
    
    def custom_callback(self, data):
        self.callback_called = True
        self.callback_data = dict(data)

    def test_listener(self):
        self.callback_called = False
        self.callback_data = None

        listener = Listener(
            port=5000,
            quiet=True,
            custom_callback=self.custom_callback
        )

        # start the listener in a separate thread
        listener_thread = threading.Thread(target=listener.start)
        listener_thread.daemon = True
        listener_thread.start()

        # give the listener some time to start
        time.sleep(0.1)

        # send the test ogg file to the listener
        with open(self.test_ogg_file, 'rb') as f:
            test_ogg_data = f.read()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('localhost', 5000))
            sock.sendall(b'SOURCE / HTTP/1.0\r\n\r\n')
            sock.sendall(test_ogg_data)

        # give the listener some time to process the data
        time.sleep(0.1)

        # verify that the custom_callback has been called with the correct metadata
        self.assertTrue(self.callback_called)
        self.assertIn('artist', self.callback_data)
        self.assertIn('title', self.callback_data)
        self.assertEqual(self.callback_data['artist'], 'Test Artist')
        self.assertEqual(self.callback_data['title'], 'Test Title')

        # stop the listener
        listener_thread.join(timeout=1)


if __name__ == '__main__':
    unittest.main()
