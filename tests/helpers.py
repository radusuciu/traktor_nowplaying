"""Shared helpers for building synthetic Ogg/Vorbis data in tests."""
import io
import os
import struct

# a tiny Ogg Vorbis stream with a single track, produced by Traktor
FIXTURE_OGG = os.path.join(os.path.dirname(__file__), 'test_single_track_1ms.ogg')


def build_comment_header(comments, vendor=b'test'):
    """Build the body of a Vorbis comment header (without the packet type/name)."""
    out = struct.pack('<I', len(vendor)) + vendor
    out += struct.pack('<I', len(comments))
    for comment in comments:
        out += struct.pack('<I', len(comment)) + comment
    return io.BytesIO(out)


def lacing(length, complete=True):
    """
    Return the segment table for a packet of `length` bytes.

    A packet is split into 255-byte segments; a final segment shorter than
    255 bytes marks its end. If `complete` is False the packet is left open
    (its final segment is a full 255 bytes) so it continues on the next page.
    """
    segments = [255] * (length // 255)
    remainder = length % 255
    if complete or remainder:
        segments.append(remainder)
    return segments


def build_page(segments, payload, pageseq=0, flags=0):
    """Build one Ogg page with the given segment table and payload bytes."""
    header = struct.pack(
        '<4sBBqIIiB',
        b'OggS', 0, flags, 0, 1, pageseq, 0, len(segments),
    )
    return header + bytes(segments) + payload
