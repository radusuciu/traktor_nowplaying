import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
import pathlib


class traktor_nowplaying(QWidget):
    def __init__(self):
        super(traktor_nowplaying, self).__init__()
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = pathlib.Path('traktor_nowplaying/ui/app.ui')
        ui_file = QFile(str(path))
        ui_file.open(QFile.ReadOnly)
        loader.load(ui_file, self)
        ui_file.close()

if __name__ == "__main__":
    app = QApplication([])
    widget = traktor_nowplaying()
    widget.show()
    sys.exit(app.exec_())
