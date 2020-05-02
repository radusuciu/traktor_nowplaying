"""
This code is modified from the tinytag project:

https://github.com/devsnd/tinytag

Original license below:

MIT License

Copyright (c) 2014-2017 Tom Wallroth

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import struct
import os
import codecs

def parse_pages(fh):
    # for the spec, see: https://wiki.xiph.org/Ogg
    previous_page = b''  # contains data from previous (continuing) pages
    header_data = fh.read(27)  # read ogg page header
    while len(header_data) != 0:
        header = struct.unpack('<4sBBqIIiB', header_data)
        oggs, version, flags, pos, serial, pageseq, crc, segments = header
        # self._max_samplenum = max(self._max_samplenum, pos)
        if oggs != b'OggS' or version != 0:
            raise Exception('Not a valid ogg file!')
        segsizes = struct.unpack('B'*segments, fh.read(segments))
        total = 0
        for segsize in segsizes:  # read all segments
            total += segsize
            if total < 255:  # less than 255 bytes means end of page
                yield previous_page + fh.read(total)
                previous_page = b''
                total = 0
        if total != 0:
            if total % 255 == 0:
                previous_page += fh.read(total)
            else:
                yield previous_page + fh.read(total)
                previous_page = b''
        header_data = fh.read(27)

def parse_comment(fh):
    # for the spec, see: http://xiph.org/vorbis/doc/v-comment.html
    # discnumber tag based on: https://en.wikipedia.org/wiki/Vorbis_comment
    # https://sno.phy.queensu.ca/~phil/exiftool/TagNames/Vorbis.html
    comment_type_to_attr_mapping = {
        'album': 'album',
        'albumartist': 'albumartist',
        'title': 'title',
        'artist': 'artist',
        'date': 'year',
        'tracknumber': 'track',
        'discnumber': 'disc',
        'genre': 'genre',
        'description': 'comment',
        'composer': 'composer',
    }
    vendor_length = struct.unpack('I', fh.read(4))[0]
    fh.seek(vendor_length, os.SEEK_CUR)  # jump over vendor
    elements = struct.unpack('I', fh.read(4))[0]

    metadata = []

    for i in range(elements):
        length = struct.unpack('I', fh.read(4))[0]
        try:
            keyvalpair = codecs.decode(fh.read(length), 'UTF-8')
        except UnicodeDecodeError:
            continue
        if '=' in keyvalpair:
            key, value = keyvalpair.split('=', 1)
            fieldname = comment_type_to_attr_mapping.get(key.lower())
            if fieldname:
                metadata.append((fieldname, value))

    return metadata
