from unittest import TestCase
from contextlib import redirect_stdout
import io
import os
import tempfile

from traktor_nowplaying.core import TrackWriter


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


class TestTrackWriterStdout(TestCase):
    def render(self, updates, **kwargs):
        """Feed each update to a writer and return everything it printed."""
        writer = TrackWriter(**kwargs)
        # capture stdout so the test does not depend on the console encoding
        # (e.g. cp1252 on Windows when output is piped)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            for update in updates:
                writer.update(update)
        return stdout.getvalue()

    def test_default_format(self):
        out = self.render([
            {'title': 'Title', 'artist': 'Artist'},
            {'title': '音楽', 'artist': 'Artist'},
        ])

        self.assertEqual(out, 'Artist - Title\nArtist - 音楽\n')

    def test_accepts_list_of_tuples(self):
        out = self.render([[('artist', 'Artist'), ('title', 'Title'), ('bpm', '128')]])

        self.assertEqual(out, 'Artist - Title\n')

    def test_custom_format(self):
        out = self.render(
            [{'title': 'Title', 'artist': 'Artist'}],
            output_format='{{title}} by {{artist}}',
        )

        self.assertEqual(out, 'Title by Artist\n')

    def test_missing_title_renders_empty(self):
        out = self.render([{'artist': 'Artist'}])

        self.assertEqual(out, 'Artist - \n')

    def test_missing_artist_renders_empty(self):
        out = self.render([{'title': 'Title'}], output_format='{{title}}')

        self.assertEqual(out, 'Title\n')

    def test_html_in_values_is_not_escaped(self):
        out = self.render([{'artist': 'Simon & Garfunkel', 'title': '<3'}])

        self.assertEqual(out, 'Simon & Garfunkel - <3\n')

    def test_html_in_format_is_kept(self):
        out = self.render(
            [{'artist': 'Artist', 'title': 'Title'}],
            output_format='<b>{{artist}}</b> - {{title}}',
        )

        self.assertEqual(out, '<b>Artist</b> - Title\n')

    def test_update_without_artist_or_title_is_ignored(self):
        out = self.render([{'bpm': '128'}, {}, []])

        self.assertEqual(out, '')

    def test_quiet_suppresses_output(self):
        out = self.render([{'artist': 'Artist', 'title': 'Title'}], quiet=True)

        self.assertEqual(out, '')

    def test_empty_render_prints_nothing(self):
        out = self.render([{'artist': 'Artist'}], output_format='{{title}}')

        self.assertEqual(out, '')


class TestTrackWriterFile(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.outfile = os.path.join(self.tmpdir.name, 'nowplaying.txt')

    def writer(self, **kwargs):
        kwargs.setdefault('quiet', True)
        kwargs.setdefault('outfile', self.outfile)
        return TrackWriter(**kwargs)

    def test_file_is_created_on_init(self):
        self.writer()

        self.assertTrue(os.path.isfile(self.outfile))
        self.assertEqual(read(self.outfile), '')

    def test_missing_parent_directories_are_created(self):
        outfile = os.path.join(self.tmpdir.name, 'a', 'b', 'nowplaying.txt')
        writer = self.writer(outfile=outfile)
        writer.update({'artist': 'Artist', 'title': 'Title'})

        self.assertEqual(read(outfile), 'Artist - Title')

    def test_outfile_pointing_to_directory_does_not_raise(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.writer(outfile=self.tmpdir.name)

        self.assertIn('Error encountered', stdout.getvalue())

    def test_overwrite_keeps_only_latest_track(self):
        writer = self.writer()
        writer.update({'artist': 'One', 'title': 'First'})
        writer.update({'artist': 'Two', 'title': 'Second'})

        self.assertEqual(read(self.outfile), 'Two - Second')

    def test_max_tracks_is_ignored_without_append(self):
        writer = self.writer(max_tracks=5)
        writer.update({'artist': 'One', 'title': 'First'})
        writer.update({'artist': 'Two', 'title': 'Second'})

        self.assertEqual(read(self.outfile), 'Two - Second')

    def test_append_keeps_all_tracks(self):
        writer = self.writer(append=True)
        for i in range(3):
            writer.update({'artist': 'Artist', 'title': str(i)})

        expected = os.linesep.join(['Artist - 0', 'Artist - 1', 'Artist - 2'])
        self.assertEqual(read(self.outfile), expected)

    def test_append_with_max_tracks_keeps_newest(self):
        writer = self.writer(append=True, max_tracks=2)
        for i in range(4):
            writer.update({'artist': 'Artist', 'title': str(i)})

        expected = os.linesep.join(['Artist - 2', 'Artist - 3'])
        self.assertEqual(read(self.outfile), expected)

    def test_multiline_format_line_endings_are_written_verbatim(self):
        writer = self.writer(output_format='{{artist}}\r\n{{title}}', append=True)
        writer.update([('artist', 'foo'), ('title', 'bar')])

        with open(self.outfile, 'rb') as f:
            self.assertEqual(f.read(), b'foo\r\nbar')

        writer.update([('artist', 'foo2'), ('title', 'bar2')])

        with open(self.outfile) as f:
            self.assertEqual(len(f.readlines()), 4)

    def test_file_is_written_as_utf8(self):
        writer = self.writer()
        writer.update({'artist': 'Björk', 'title': '音楽'})

        with open(self.outfile, 'rb') as f:
            self.assertEqual(f.read(), 'Björk - 音楽'.encode('utf-8'))

    def test_template_receives_tracks(self):
        template = '% for track in tracks:\n{{track["title"]}}\n% end\n'
        writer = self.writer(template=template, append=True)
        writer.update({'artist': 'Artist', 'title': 'First'})
        writer.update({'artist': 'Artist', 'title': 'Second'})

        self.assertEqual(read(self.outfile), 'First\nSecond\n')

    def test_template_overrides_format(self):
        writer = self.writer(template='{{tracks[-1]["artist"]}}', output_format='{{title}}')
        writer.update({'artist': 'Artist', 'title': 'Title'})

        self.assertEqual(read(self.outfile), 'Artist')

    def test_template_escapes_html_by_default(self):
        # unlike --format, templates are meant for HTML output so bottle's
        # escaping is left in place
        writer = self.writer(template='{{tracks[-1]["artist"]}}')
        writer.update({'artist': 'Simon & Garfunkel', 'title': 'Title'})

        self.assertEqual(read(self.outfile), 'Simon &amp; Garfunkel')

    def test_track_without_artist_or_title_does_not_touch_file(self):
        writer = self.writer()
        writer.update({'artist': 'Artist', 'title': 'Title'})
        writer.update({'bpm': '128'})

        self.assertEqual(read(self.outfile), 'Artist - Title')

    def test_stdout_and_file_together(self):
        writer = self.writer(quiet=False)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            writer.update({'artist': 'Artist', 'title': 'Title'})

        self.assertEqual(stdout.getvalue(), 'Artist - Title\n')
        self.assertEqual(read(self.outfile), 'Artist - Title')
