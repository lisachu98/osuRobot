import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog)
from PyQt5.Qt import Qt
import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import pyfirmata
from gui import Ui_MainWindow

ratio = 0.5

kit = MotorKit(i2c=board.I2C())
board = pyfirmata.Arduino('/dev/ttyACM0')
it = pyfirmata.util.Iterator(board)
it.start()
board.digital[6].mode = pyfirmata.INPUT


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.wczytaj)
        self.pushButton_2.clicked.connect(self.start)
        self.lines = []
        self.x = 0
        self.y = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self.start()
        if event.key() == Qt.Key_K:
            self.pozycjaPocz()

    def goTo(self, x, y):
        xTmp = self.x
        if x > xTmp:
            for i in range(int((x - xTmp) * ratio)):
                kit.stepper1.onestep(direction=stepper.BACKWARD)
            self.x += int((x - xTmp) * ratio)
        if x < xTmp:
            for i in range(int((xTmp - x) * ratio)):
                kit.stepper1.onestep()
            self.x -= int((xTmp - x) * ratio)

    def wczytaj(self):
        path, _ = QFileDialog.getOpenFileName(None, "Wybierz mape", "/home/lisachu/Desktop/Songs",
                                              "osu! beatmap (*.osu)")
        if path == '':
            return
        with open(path) as f:
            lines = f.readlines()
        self.label_5.setText(lines[22][13:])
        self.label_6.setText(lines[24][14:])
        self.label_7.setText(lines[25][8:])
        self.label_8.setText(lines[26][8:])

        indeks = 0
        for line in lines:
            indeks += 1
            if line == "[HitObjects]\n":
                break
        lines = lines[indeks:]
        for i in range(len(lines)):
            lines[i] = lines[i].split(",")
        for i in range(len(lines)):
            lines[i] = lines[i][:3]
        for i in range(len(lines)):
            lines[i][2] = int(lines[i][2])
            lines[i][1] = int(lines[i][1])
            lines[i][0] = int(lines[i][0])
        czasStart = lines[0][2]
        for i in range(len(lines)):
            lines[i][2] = (lines[i][2] - czasStart) / 1000
        self.lines = lines
        self.label_10.setText(str(lines[len(lines) - 1][2]) + "s")
        self.pushButton_2.setEnabled(1)
        self.pozycjaPocz()
        print("Rysik na (" + str(lines[0][0]) + ";" + str(lines[0][1]) + ")")
        self.goTo(lines[0][0], 0)

    def pozycjaPocz(self):
        while True:
            kit.stepper1.onestep()
            sw = board.digital[6].read()
            if sw is True:
                self.x = 0
                break

    def start(self):
        tmpLines = self.lines[1:]
        koniec = tmpLines[len(tmpLines) - 1][2] - tmpLines[0][2]
        czas = 0.0
        self.progressBar.setTextVisible(1)
        print("Rysik na (" + str(tmpLines[0][0]) + ";" + str(tmpLines[0][1]) + ")")
        self.goTo(tmpLines[0][0], 0)
        while czas < koniec:
            time.sleep(0.01)
            czas += 0.01
            if czas > tmpLines[0][2]:
                tmpLines = tmpLines[1:]
                print("Rysik na (" + str(tmpLines[0][0]) + ";" + str(tmpLines[0][1]) + ")")
                self.goTo(tmpLines[0][0], 0)
            self.progressBar.setValue(int(czas * 100 / koniec))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())