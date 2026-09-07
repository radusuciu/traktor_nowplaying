from unittest import TestCase, mock
from contextlib import redirect_stdout
import io
import os
import tempfile

from traktor_nowplaying import cli
from traktor_nowplaying.version import __version__


class TestArgumentParsing(TestCase):
    def test_defaults(self):
        args = cli.parser.parse_args([])

        self.assertEqual(args.port, 8000)
        self.assertFalse(args.quiet)
        self.assertEqual(args.format, '{{artist}} - {{title}}')
        self.assertIsNone(args.outfile)
        self.assertIsNone(args.template)
        self.assertFalse(args.append)
        self.assertIsNone(args.max_tracks)
        self.assertFalse(args.interactive)

    def test_all_options(self):
        args = cli.parser.parse_args([
            '-p', '9000',
            '-q',
            '-f', '{{title}}',
            '-o', 'out.txt',
            '-t', 'template.html',
            '-a',
            '-m', '5',
            '-i',
        ])

        self.assertEqual(args.port, 9000)
        self.assertTrue(args.quiet)
        self.assertEqual(args.format, '{{title}}')
        self.assertEqual(args.outfile, 'out.txt')
        self.assertEqual(args.template, 'template.html')
        self.assertTrue(args.append)
        self.assertEqual(args.max_tracks, 5)
        self.assertTrue(args.interactive)

    def test_long_options(self):
        args = cli.parser.parse_args([
            '--port', '9000', '--quiet', '--outfile', 'out.txt',
            '--append', '--max-tracks', '5',
        ])

        self.assertEqual(args.port, 9000)
        self.assertTrue(args.quiet)
        self.assertEqual(args.outfile, 'out.txt')
        self.assertTrue(args.append)
        self.assertEqual(args.max_tracks, 5)

    def test_non_integer_port_is_rejected(self):
        with redirect_stdout(io.StringIO()), mock.patch('sys.stderr', io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.parser.parse_args(['--port', 'abc'])

        self.assertNotEqual(ctx.exception.code, 0)

    def test_version(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as ctx:
                cli.parser.parse_args(['--version'])

        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(stdout.getvalue().strip(), f'traktor_nowplaying {__version__}')


class TestReadTemplateFile(TestCase):
    def test_reads_file_contents(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'template.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('{{tracks}}')

            self.assertEqual(cli._read_template_file(path), '{{tracks}}')

    def test_missing_file_prints_error_and_returns_none(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = cli._read_template_file('/does/not/exist.html')

        self.assertIsNone(result)
        self.assertIn('Error encountered', stdout.getvalue())


@mock.patch('traktor_nowplaying.cli.Listener')
class TestMain(TestCase):
    def run_main(self, argv):
        with mock.patch('sys.argv', ['traktor_nowplaying'] + argv):
            cli.main()

    def test_options_are_passed_to_listener(self, Listener):
        self.run_main(['-p', '9000', '-q', '-f', '{{title}}', '-o', 'out.txt', '-a', '-m', '5'])

        Listener.assert_called_once_with(
            port=9000,
            quiet=True,
            output_format='{{title}}',
            outfile='out.txt',
            template=None,
            append=True,
            max_tracks=5,
        )
        Listener.return_value.start.assert_called_once_with()

    def test_template_file_contents_are_passed(self, Listener):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'template.html')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('{{tracks}}')

            self.run_main(['-q', '-t', path])

        self.assertEqual(Listener.call_args.kwargs['template'], '{{tracks}}')

    def test_missing_template_file_falls_back_to_no_template(self, Listener):
        with redirect_stdout(io.StringIO()):
            self.run_main(['-q', '-t', '/does/not/exist.html'])

        self.assertIsNone(Listener.call_args.kwargs['template'])

    def test_no_arguments_offers_interactive_mode(self, Listener):
        # pressing Enter at the prompt continues with the defaults
        with mock.patch('builtins.input', return_value=''):
            self.run_main([])

        self.assertEqual(Listener.call_args.kwargs['port'], 8000)
        self.assertFalse(Listener.call_args.kwargs['quiet'])

    def test_interactive_flag_overrides_command_line(self, Listener):
        answers = iter(['', 'y', ''])  # default port, quiet, no outfile
        with mock.patch('builtins.input', side_effect=lambda *_: next(answers)):
            with redirect_stdout(io.StringIO()):
                self.run_main(['-i', '-p', '9000'])

        self.assertEqual(Listener.call_args.kwargs['port'], 8000)
        self.assertTrue(Listener.call_args.kwargs['quiet'])


class TestInteractive(TestCase):
    def interactive(self, answers):
        answers = iter(answers)
        with mock.patch('builtins.input', side_effect=lambda *_: next(answers)):
            with redirect_stdout(io.StringIO()):
                return cli.interactive()

    def test_all_defaults(self):
        self.assertEqual(self.interactive(['', '', '']), [])

    def test_custom_port(self):
        self.assertEqual(self.interactive(['9000', '', '']), ['--port', '9000'])

    def test_invalid_port_is_asked_again(self):
        self.assertEqual(self.interactive(['abc', '0', '70000', '9000', '', '']), ['--port', '9000'])

    def test_quiet_accepts_yes_variants(self):
        self.assertEqual(self.interactive(['', 'y', '']), ['--quiet'])
        self.assertEqual(self.interactive(['', 'Yes', '']), ['--quiet'])
        self.assertEqual(self.interactive(['', 'n', '']), [])

    def test_outfile_with_append_and_max_tracks(self):
        args = self.interactive(['', '', 'out.txt', 'y', '5'])

        self.assertEqual(args, ['--outfile', 'out.txt', '--append', '--max-tracks', '5'])

    def test_outfile_without_append_skips_max_tracks(self):
        self.assertEqual(self.interactive(['', '', 'out.txt', 'n']), ['--outfile', 'out.txt'])

    def test_invalid_max_tracks_is_ignored(self):
        args = self.interactive(['', '', 'out.txt', 'y', 'lots'])

        self.assertEqual(args, ['--outfile', 'out.txt', '--append'])

    def test_result_is_parseable(self):
        args = cli.parser.parse_args(self.interactive(['9000', 'y', 'out.txt', 'y', '5']))

        self.assertEqual(args.port, 9000)
        self.assertTrue(args.quiet)
        self.assertEqual(args.outfile, 'out.txt')
        self.assertTrue(args.append)
        self.assertEqual(args.max_tracks, 5)
