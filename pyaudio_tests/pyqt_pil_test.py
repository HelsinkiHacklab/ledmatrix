#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui
import Image
import ImageQt


class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 400, 293)
        self.setWindowTitle('My Widget!')


        PilImage = Image.open('kitten1.jpg')
        QtImage1 = ImageQt.ImageQt(PilImage)
        QtImage2 = QtImage1.copy()
        pixmap = QtGui.QPixmap.fromImage(QtImage2)
        label = QtGui.QLabel('', self)
        label.setPixmap(pixmap)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWidget = MyWidget()
    myWidget.show()

    sys.exit(app.exec_())

