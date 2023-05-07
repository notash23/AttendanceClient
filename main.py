from enum import Enum
import json
import socket
import sys
import time
import numpy as np
import cv2
import threading
import pyzbar.pyzbar as bar
import OPi.GPIO as GPIO
from OPi.constants import GPIO as GPIO_CONST

SERVER = "192.168.100.89"
PORT = 5050
ADDR = (SERVER, PORT)
HEADER = 4
OPCODE = 1
FORMAT = 'utf-8'
CAMERA_VIEW = 'CameraView'


def decrypt(InString):
    ValueSet = InString.split("!")
    OutString = ""
    try:
        for char in ValueSet[0]:
            OutString += chr(ord(char) + int(ValueSet[1]) - len(ValueSet[0]))
    except IndexError:
        return ""
    return OutString


class State(Enum):
    SHUT_DOWN = -1
    DISCONNECTED = 0
    SCAN = 1
    SUCCESS = 2
    ERROR = 3
    LOADING = 4
    STAFF_SELECT = 5


class OpCode(Enum):
    CONNECT = 0
    ATTENDANCE = 1
    STAFF_ATTENDANCE = 2
    SUCCESSFUL = 3
    UNSUCCESSFUL = 4
    DISCONNECT = 5


class Server:
    def __init__(self):
        self.state = State.DISCONNECTED
        self.response = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread(target=self.awaitConnection).start()

    def awaitConnection(self):
        self.server.settimeout(5)
        while self.server.connect_ex(ADDR) != 0:
            if self.state == State.SHUT_DOWN:
                return
            print("Trying to connect to server...")
            time.sleep(5)
        print("We have connected!")
        self.server.settimeout(None)
        with open(r'resources/authData.json', 'r') as f:
            self.__send(OpCode.CONNECT, json.loads(f.read()))
            f.close()
        response = self.__receive()
        if not response:
            return
        if response[0] == OpCode.DISCONNECT.value:
            self.state = State.ERROR
            self.server.close()
            time.sleep(2)
            self.state = State.DISCONNECTED
            return
        if response[0] == OpCode.SUCCESSFUL.value:
            self.state = State.SCAN

    def shutdown(self):
        self.__send(OpCode.DISCONNECT)
        self.state = State.SHUT_DOWN

    def setLoading(self):
        self.state = State.LOADING

    def sendAttendance(self, msg):
        self.__send(OpCode.ATTENDANCE, {"attendanceString": msg})
        response = self.__receive()
        if not response:
            return
        if response[0] == OpCode.SUCCESSFUL.value:
            self.response = response[1]
            self.state = State.SUCCESS
        elif response[0] == OpCode.UNSUCCESSFUL.value:
            self.response = response[1]
            self.state = State.ERROR
            time.sleep(2)
            self.state = State.SCAN
        elif response[0] == OpCode.STAFF_ATTENDANCE.value:
            self.response = response[1]
            self.state = State.STAFF_SELECT

    def respondStaffLeave(self, accept):
        if self.state != State.STAFF_SELECT:
            return
        self.state = State.LOADING
        if accept:
            self.__send(OpCode.STAFF_ATTENDANCE, {"setLeave": "yes"})
            response = self.__receive()
            if not response:
                return
            if response[0] == OpCode.SUCCESSFUL.value:
                self.response = response[1]
                self.state = State.SUCCESS
            elif response[0] == OpCode.UNSUCCESSFUL.value:
                self.state = State.ERROR
                time.sleep(2)
                self.state = State.SCAN
        else:
            self.__send(OpCode.STAFF_ATTENDANCE)

    def setState(self, state):
        self.state = state

    def __send(self, opcode, outJson=None):
        if outJson is None:
            outJson = {}
        jsonStr = json.dumps(outJson)
        msg = jsonStr.encode(FORMAT)
        msg_length = len(msg)
        self.server.send(opcode.value.to_bytes(length=OPCODE, byteorder=sys.byteorder, signed=False))
        self.server.send(msg_length.to_bytes(length=HEADER, byteorder=sys.byteorder, signed=False))
        self.server.send(msg)

    def __receive(self):
        opcode = self.server.recv(OPCODE)
        if opcode:
            opcode = int.from_bytes(opcode, sys.byteorder)
        msg_length = self.server.recv(HEADER)
        if msg_length:
            msg_length = int.from_bytes(msg_length, sys.byteorder)
            return opcode, json.loads(self.server.recv(msg_length).decode(FORMAT))


def main():
    gifCap = cv2.VideoCapture(r'resources/nyan-cat.mp4')
    nyan_fps = 1000 / gifCap.get(cv2.CAP_PROP_FPS)
    nyan_frames = []

    # Play the video once and store the frames in an array
    while gifCap.isOpened():
        _ret, f = gifCap.read()
        if f is None:
            break
        nyan_frames.append(f)
    gifCap.release()

    gifCap = cv2.VideoCapture(r'resources/borat-nice.mp4')
    borat_fps = 1000 / gifCap.get(cv2.CAP_PROP_FPS)
    borat_frames = []

    # Play the video once and store the frames in an array
    while gifCap.isOpened():
        _ret, f = gifCap.read()
        if f is None:
            break
        borat_frames.append(f)
    gifCap.release()

    cv2.namedWindow(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)
    font = cv2.FONT_HERSHEY_TRIPLEX

    server = Server()
    GPIO.setmode(GPIO_CONST.SUNXI)
    buttons = ["PC8", "PC11"]
    GPIO.setup(buttons, GPIO_CONST.IN, GPIO_CONST.HIGH)
    GPIO.add_event_detect(buttons[0], GPIO_CONST.FALLING, callback=server.respondStaffLeave(True))
    GPIO.add_event_detect(buttons[1], GPIO_CONST.FALLING, callback=server.respondStaffLeave(False))

    # Makes a loading animation while waiting for connection
    dots = '.'
    index = 0
    while server.state == State.DISCONNECTED:
        if index == len(nyan_frames) - 1:
            index = 0
        else:
            index += 1

        if len(dots) > 3:
            dots = '.'
        else:
            dots += '.'
        frame = cv2.putText(nyan_frames[index], f"Connecting{dots}", (20, 50), font, 0.7, (255, 255, 255))
        cv2.imshow(CAMERA_VIEW, frame)
        cv2.waitKey(int(nyan_fps))

    cap = cv2.VideoCapture(0)

    # Matches state to show frame
    while server.state != State.DISCONNECTED:
        success, frame = cap.read()
        if server.state == State.SCAN:
            if cap.isOpened():
                for barcode in bar.decode(frame):
                    myData = barcode.data.decode('utf-8')
                    try:
                        if myData is not None:
                            server.setLoading()
                            threading.Thread(target=server.sendAttendance, args=(myData,)).start()
                    except KeyboardInterrupt:
                        raise Exception("error")
                cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.LOADING:
            frame = np.full([400, 400, 3], (255, 255, 255), dtype=np.uint8)
            cv2.putText(frame, "Loading", (100, 200), font, 0.6, (0, 0, 0), 2)
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.SUCCESS:
            for frame in borat_frames:
                cv2.putText(frame, server.response["Name"], (100, 100), font, 1, (255, 255, 255))
                cv2.imshow(CAMERA_VIEW, frame)
                cv2.waitKey(int(borat_fps))
            server.setState(State.SCAN)
        elif server.state == State.STAFF_SELECT:
            frame = np.full([400, 400, 3], (255, 255, 255), dtype=np.uint8)
            cv2.putText(frame, "Are you leaving?", (100, 100), font, 1, (0, 0, 0))
            cv2.putText(frame, server.response["Surname"], (100, 200), font, 1, (255, 255, 255))
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.ERROR:
            frame = np.full([400, 400, 3], 1, dtype=np.uint8)
            cv2.putText(frame, "ERROR", (200, 200), font, 0.6,
                        (0, 0, 255), 2)
            cv2.imshow(CAMERA_VIEW, frame)
        else:
            success, frame = cap.read()
            cv2.imshow(CAMERA_VIEW, frame)
        cv2.waitKey(1)
        if cv2.getWindowProperty(CAMERA_VIEW, cv2.WND_PROP_VISIBLE) < 1:
            break
    cap.release()
    cv2.destroyAllWindows()
    server.shutdown()


if __name__ == "__main__":
    main()
