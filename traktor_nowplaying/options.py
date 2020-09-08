PORT = 8000
QUIET = False
OUTPUT_FORMAT = '{{artist}} - {{title}}'
USE_DEFAULT_HTML_TEMPLATE = False
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
    <body>
        {tracklist}
    </body>
</html>
'''
INTERACTIVE = False
APPEND = False
MAX_TRACKS = -1
