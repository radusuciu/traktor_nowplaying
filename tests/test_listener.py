from unittest import TestCase
import os
import socket
import tempfile
import threading
import time

from traktor_nowplaying.core import Listener

from .helpers import FIXTURE_OGG


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def connect_with_retry(port, timeout=5):
    """Connect to the listener, retrying until it has bound its socket."""
    deadline = time.monotonic() + timeout
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('127.0.0.1', port))
            return sock
        except OSError:
            sock.close()
            if time.monotonic() > deadline:
                raise
            time.sleep(0.02)


class TestListener(TestCase):
    def start_listener(self, **kwargs):
        """Start a listener on a free port in a background thread; returns the port."""
        port = free_port()
        listener = Listener(port=port, **kwargs)
        # serve_forever never returns, so the thread is a daemon and is simply
        # abandoned once the test finishes
        thread = threading.Thread(target=listener.start, daemon=True)
        thread.start()
        return port

    def send_fixture(self, port):
        with open(FIXTURE_OGG, 'rb') as f:
            data = f.read()

        with connect_with_retry(port) as sock:
            sock.sendall(b'SOURCE / HTTP/1.0\r\n\r\n')
            sock.sendall(data)

    def test_custom_callback_receives_metadata(self):
        received = []
        done = threading.Event()

        def callback(data):
            received.append(data)
            done.set()

        port = self.start_listener(quiet=True, custom_callback=callback)
        self.send_fixture(port)

        self.assertTrue(done.wait(timeout=5), 'callback was not called')
        self.assertEqual(len(received), 1)
        # callbacks get the raw list of (field, value) tuples
        self.assertIsInstance(received[0], list)
        self.assertEqual(dict(received[0]), {'artist': 'Test Artist', 'title': 'Test Title'})

    def test_writes_outfile_and_calls_callback(self):
        done = threading.Event()

        with tempfile.TemporaryDirectory() as d:
            outfile = os.path.join(d, 'nowplaying.txt')
            port = self.start_listener(
                quiet=True,
                outfile=outfile,
                custom_callback=lambda data: done.set(),
            )
            self.send_fixture(port)

            # the writer callback runs before the custom callback for each packet
            self.assertTrue(done.wait(timeout=5), 'callback was not called')
            with open(outfile, encoding='utf-8') as f:
                self.assertEqual(f.read(), 'Test Artist - Test Title')
