import os
import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog)
from PyQt5.Qt import Qt
from picamera.array import PiRGBArray # Generates a 3D RGB array
from picamera import PiCamera
import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import pyfirmata
from gui import Ui_MainWindow

ratio = 0.5

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
raw_capture = PiRGBArray(camera, size=(640, 480))
kit = MotorKit(i2c=board.I2C())
board = pyfirmata.Arduino('/dev/ttyACM0')
it = pyfirmata.util.Iterator(board)
it.start()
board.digital[6].mode = pyfirmata.INPUT
board.digital[7].mode = pyfirmata.INPUT
board.digital[8].mode = pyfirmata.INPUT

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.wczytaj)
        self.pushButton_2.clicked.connect(self.start)
        self.lines = []
        self.x = 0
        self.y = 0
        self.prawo = 0
        self.dol = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self.start()
        if event.key() == Qt.Key_A:
            self.wczytaj()
        if event.key() == Qt.Key_K:
            self.pozycjaPocz()
        if event.key() == Qt.Key_F:
            kit.stepper2.onestep(style=stepper.DOUBLE)
            self.dol += 1
            print("y: " + str(self.dol))
        if event.key() == Qt.Key_G:
            kit.stepper1.onestep(style=stepper.DOUBLE)
            self.prawo += 1
            print("x: " + str(self.prawo))
        if event.key() == Qt.Key_R:
            kit.stepper2.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
        if event.key() == Qt.Key_D:
            kit.stepper1.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)

    def check(image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(image, (0, 50, 20), (5, 255, 255))
        mask2 = cv2.inRange(image, (175, 50, 20), (180, 255, 255))
        mask = cv2.bitwise_or(mask1, mask2)
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
            if cv2.contourArea(cnt) > 100 and len(approx) > 7:
                return True
        return False

    def goTo(self, x, y):
        while True:
            if self.x == x and self.y == y:
                break
            if self.x != x:
                if x > self.x:
                    kit.stepper1.onestep(style=stepper.DOUBLE)
                    self.x += 1
                else:
                    kit.stepper1.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
                    self.x -= 1
            if self.y != y:
                if y > self.y:
                    kit.stepper2.onestep(style=stepper.DOUBLE)
                    self.y += 1
                else:
                    kit.stepper2.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
                    self.y -= 1

    def reset(self):
        board.digital[10].write(0)
        board.digital[11].write(0)
        self.pushButton_2.setEnabled(0)
        self.progressBar.setTextVisible(0)
        self.progressBar.setValue(0)

    def wczytaj(self):
        with open("/media/pi/NEW VOLUME/osuRobot/Song/" + os.listdir("/media/pi/NEW VOLUME/osuRobot/Song")[0]) as f:
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
            lines[i][1] = int(int(lines[i][1]) * ratio)
            lines[i][0] = int(int(lines[i][0]) * ratio)
        czasStart = lines[0][2]
        for i in range(len(lines)):
            lines[i][2] = (lines[i][2] - czasStart) / 1000
        self.lines = lines
        self.label_10.setText(str(lines[len(lines) - 1][2]) + "s")
        self.pushButton_2.setEnabled(1)
        self.pozycjaPocz()
        print("Rysik na (" + str(lines[0][0]) + ";" + str(lines[0][1]) + ")")
        self.goTo(lines[0][0], lines[0][1])
        board.digital[10].write(1)
        for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
            image = frame.array
            if self.check(image):
                break
            raw_capture.truncate(0)
        time.sleep(1)
        self.start()

    def pozycjaPocz(self):
        while True:
            sw = board.digital[6].read()
            if sw is True:
                self.x = 0
                break
            kit.stepper1.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
        while True:
            sw = board.digital[7].read()
            if sw is True:
                self.y = 0
                break
            kit.stepper2.onestep(style=stepper.DOUBLE, direction=stepper.BACKWARD)
        self.goTo(98, 51)
        self.x = 0
        self.y = 0

    def start(self):
        startTime = time.time()
        tmpLines = self.lines[1:]
        koniec = tmpLines[len(tmpLines) - 1][2] - tmpLines[0][2]
        self.progressBar.setTextVisible(1)
        board.digital[11].write(1)
        print("Rysik na (" + str(tmpLines[0][0]) + ";" + str(tmpLines[0][1]) + ")")
        self.goTo(tmpLines[0][0], tmpLines[0][1])
        while len(tmpLines) > 1:
            sw = board.digital[8].read()
            if sw is True:
                break
            time.sleep(0.001)
            stepTime = time.time()
            if stepTime - startTime > tmpLines[0][2]:
                tmpLines = tmpLines[1:]
                print("Rysik na (" + str(tmpLines[0][0]) + ";" + str(tmpLines[0][1]) + ")")
                self.goTo(tmpLines[0][0], tmpLines[0][1])
            self.progressBar.setValue(int((stepTime - startTime) * 100 / koniec))
        self.reset()

if __name__ == "__main__":
    board.digital[9].write(1)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())