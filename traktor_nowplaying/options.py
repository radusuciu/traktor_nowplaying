PORT = 8000
QUIET = False
OUTPUT_FORMAT = '{{artist}} - {{title}}'
USE_DEFAULT_HTML_TEMPLATE = False
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
    <body>
        % for track in tracks:
        <p>{{track.get('artist', '')}} - {{track.get('title')}}</p>
        % end
    </body>
</html>
'''
INTERACTIVE = False
APPEND = False
MAX_TRACKS = -1
