
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
import sys

app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec_())
