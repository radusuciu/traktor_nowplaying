from PySide2.QtWidgets import *
from core import Listener
from options import PORT
from PySide2.QtCore import Signal, Slot, Qt, QUrl, QThread, QObject
from PySide2.QtGui import QPalette, QColor
from PySide2.QtQml import QQmlApplicationEngine

from PySide2 import QtCore, QtWidgets, QtQml


app = QApplication([])
app.setStyle('Fusion')
default_palette = QPalette()
dark_palette = QPalette()
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.WindowText, Qt.white)
dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
dark_palette.setColor(QPalette.ToolTipText, Qt.white)
dark_palette.setColor(QPalette.Text, Qt.white)
dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ButtonText, Qt.white)
dark_palette.setColor(QPalette.BrightText, Qt.red)
dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.HighlightedText, Qt.black)
app.setPalette(dark_palette)


window = QWidget()

layout = QGridLayout() # GRID LAYOUT


def _update_labels(info):
    artist.setText(info.get('artist', ''))
    title.setText(info.get('title', ''))

@Slot()
def listen():
    listener = Listener(port=PORT)
    state.setText('Listening.')
    listener.start()

artist_label = QLabel('Artist')
title_label = QLabel('Title')
artist = QLabel('-')
title = QLabel('-')
status = QLabel('Traktor not connected.')
state = QLabel('Not listening.')
port_label = QLabel('Port:')
outfile_label = QLabel('Output to file:')
port_input = QLineEdit(str(PORT))
outfile_input = QLineEdit('')
listen_button = QPushButton('Listen')
listen_button.clicked.connect(listen)

layout.addWidget(artist_label, 0, 0, 1, 1)
layout.addWidget(title_label, 0, 1, 1, 2)
layout.addWidget(artist, 1, 0, 1, 1)
layout.addWidget(title, 1, 1, 1, 2)
layout.addWidget(status, 2, 0, 1, 3)
layout.addWidget(state, 3, 0, 1, 3)
layout.addWidget(port_label, 4, 0, 1, 1)
layout.addWidget(port_input, 4, 1, 1, 2)
layout.addWidget(outfile_label, 5, 0, 1, 1)
layout.addWidget(outfile_input, 5, 1, 1, 2)
layout.addWidget(listen_button, 6, 2, 1, 1)

window.setLayout(layout)

window.show()

app.exec_()
