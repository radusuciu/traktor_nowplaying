import http.server
import socketserver



class APIHandler(http.server.BaseHTTPRequestHandler):
    """Simpler handler for web api."""

    def do_GET(self):
        # we send response
        self.send_response(200)
        # and headers
        self.end_headers()

    def log_request(self, code='-', size='-'):
        """Do not log messages about HTTP requests."""
        pass

    def log_error(self, format, *args):
        """Do not log messages about HTTP requests."""
        pass

with socketserver.TCPServer(('', 8222), APIHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
