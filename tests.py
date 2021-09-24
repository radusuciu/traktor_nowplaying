from unittest import TestCase
import unittest
import tempfile
import os

from traktor_nowplaying.core import TrackWriter


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


if __name__ == '__main__':
    unittest.main()
