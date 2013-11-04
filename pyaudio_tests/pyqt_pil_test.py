#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui
#import Image
import ImageQt
from PIL import Image, ImageOps


class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 400, 293)
        self.setWindowTitle('My Widget!')


        self.label = QtGui.QLabel('', self)
        self.PilImage = Image.open('kitten1.jpg')
        self.update_image()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.invert)
        self.timer.start(2500)

    def update_image(self):
        QtImage1 = ImageQt.ImageQt(self.PilImage)
        QtImage2 = QtImage1.copy()
        pixmap = QtGui.QPixmap.fromImage(QtImage2)
        self.label.setPixmap(pixmap)

    def invert(self):
        self.PilImage = ImageOps.invert(self.PilImage)
        self.update_image()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWidget = MyWidget()
    myWidget.show()
    sys.exit(app.exec_())

