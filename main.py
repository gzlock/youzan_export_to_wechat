import sys
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from ui.launch_window import LaunchWindow

if __name__ == '__main__':

    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile('main.png', QSize(16, 16))
    app_icon.addFile('main.png', QSize(24, 24))
    app_icon.addFile('main.png', QSize(32, 32))
    app_icon.addFile('main.png', QSize(48, 48))
    app_icon.addFile('main.png', QSize(256, 256))
    app.setWindowIcon(app_icon)
    w = LaunchWindow()
    w.show()
    sys.exit(app.exec_())
