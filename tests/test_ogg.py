from unittest import TestCase
import io
import struct

from traktor_nowplaying.ogg import parse_comment, parse_pages

from .helpers import FIXTURE_OGG, build_comment_header, build_page, lacing


class TestParsePages(TestCase):
    def test_multiple_packets_on_one_page(self):
        first = b'a' * 100
        second = b'b' * 50
        page = build_page(lacing(100) + lacing(50), first + second)

        self.assertEqual(list(parse_pages(io.BytesIO(page))), [first, second])

    def test_packet_spanning_multiple_segments(self):
        packet = bytes(range(256)) * 3  # 768 bytes -> segments 255, 255, 255, 3
        page = build_page(lacing(len(packet)), packet)

        self.assertEqual(list(parse_pages(io.BytesIO(page))), [packet])

    def test_packet_continued_on_next_page(self):
        head = b'x' * 510  # two full segments, packet left open
        tail = b'y' * 10
        stream = (
            build_page(lacing(510, complete=False), head, pageseq=0)
            + build_page(lacing(10), tail, pageseq=1)
        )

        self.assertEqual(list(parse_pages(io.BytesIO(stream))), [head + tail])

    def test_packets_across_consecutive_pages(self):
        stream = (
            build_page(lacing(5), b'first', pageseq=0)
            + build_page(lacing(6), b'second', pageseq=1)
        )

        self.assertEqual(list(parse_pages(io.BytesIO(stream))), [b'first', b'second'])

    def test_empty_stream_yields_nothing(self):
        self.assertEqual(list(parse_pages(io.BytesIO(b''))), [])

    def test_invalid_capture_pattern_raises(self):
        page = build_page(lacing(3), b'abc')
        bad = b'NOPE' + page[4:]

        with self.assertRaises(Exception):
            list(parse_pages(io.BytesIO(bad)))

    def test_unsupported_version_raises(self):
        page = bytearray(build_page(lacing(3), b'abc'))
        page[4] = 1  # stream structure version, must be 0

        with self.assertRaises(Exception):
            list(parse_pages(io.BytesIO(bytes(page))))

    def test_fixture_contains_vorbis_headers_in_order(self):
        with open(FIXTURE_OGG, 'rb') as f:
            packets = list(parse_pages(f))

        header_types = [p[:7] for p in packets[:3]]
        self.assertEqual(header_types, [b'\x01vorbis', b'\x03vorbis', b'\x05vorbis'])

    def test_fixture_comment_packet_parses(self):
        with open(FIXTURE_OGG, 'rb') as f:
            comment_packet = [p for p in parse_pages(f) if p[:7] == b'\x03vorbis'][0]

        walker = io.BytesIO(comment_packet)
        walker.seek(7)
        metadata = parse_comment(walker)

        self.assertEqual(dict(metadata), {'artist': 'Test Artist', 'title': 'Test Title'})


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
            b'DISCNUMBER=1',
            b'DESCRIPTION=notes',
        ]))

        self.assertEqual(metadata, [
            ('year', '2024'),
            ('track', '3'),
            ('disc', '1'),
            ('comment', 'notes'),
        ])

    def test_no_comments(self):
        self.assertEqual(parse_comment(build_comment_header([])), [])

    def test_vendor_string_is_skipped(self):
        metadata = parse_comment(build_comment_header(
            [b'TITLE=Song'],
            vendor=b'ARTIST=Not An Artist',
        ))

        self.assertEqual(metadata, [('title', 'Song')])

    def test_entries_without_equals_are_dropped(self):
        metadata = parse_comment(build_comment_header([
            b'garbage',
            b'TITLE=Song',
        ]))

        self.assertEqual(metadata, [('title', 'Song')])

    def test_value_may_contain_equals(self):
        metadata = parse_comment(build_comment_header([b'TITLE=a=b=c']))

        self.assertEqual(metadata, [('title', 'a=b=c')])

    def test_empty_value_is_kept(self):
        metadata = parse_comment(build_comment_header([b'ARTIST=']))

        self.assertEqual(metadata, [('artist', '')])

    def test_unicode_values(self):
        metadata = parse_comment(build_comment_header([
            'TITLE=音楽'.encode('utf-8'),
            'ARTIST=Björk'.encode('utf-8'),
        ]))

        self.assertEqual(metadata, [('title', '音楽'), ('artist', 'Björk')])

    def test_undecodable_entry_is_skipped(self):
        metadata = parse_comment(build_comment_header([
            b'ARTIST=\xff\xfe',
            b'TITLE=Song',
        ]))

        self.assertEqual(metadata, [('title', 'Song')])

    def test_duplicate_keys_are_all_kept(self):
        metadata = parse_comment(build_comment_header([
            b'ARTIST=One',
            b'ARTIST=Two',
        ]))

        self.assertEqual(metadata, [('artist', 'One'), ('artist', 'Two')])
