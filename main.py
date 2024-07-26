from enum import Enum
import json
import socket
import sys
import time
import numpy as np
import cv2
import threading
import pyzbar.pyzbar as bar
import os

SERVER = "192.168.100.100"
PORT = 5050
ADDR = (SERVER, PORT)
HEADER = 4
OPCODE = 1
FORMAT = 'utf-8'
CAMERA_VIEW = 'CameraView'
font = cv2.FONT_HERSHEY_SIMPLEX

absolute_path = os.path.dirname(__file__)


def decrypt(in_string):
    value_set = in_string.split("!")
    out_string = ""
    try:
        for char in value_set[0]:
            out_string += chr(ord(char) + int(value_set[1]) - len(value_set[0]))
    except IndexError:
        return ""
    return out_string


def make_paragraph(in_string: str):
    string_dimensions = cv2.getTextSize(in_string, font, 1, 2)
    if string_dimensions[0][0] < 460:
        return [(in_string, string_dimensions[0])], string_dimensions[0][1]
    words = in_string.split()
    lines = []
    current_line = ""
    height = 0
    for word in words:
        current_line_dimension = cv2.getTextSize(current_line + word + " ", font, 1, 2)
        if current_line_dimension[0][0] < 460:
            current_line += word + " "
        else:
            string_dimensions = cv2.getTextSize(current_line[:-1], font, 1, 2)
            lines.append((current_line[:-1], string_dimensions[0]))
            height += string_dimensions[0][1] + 15
            current_line = word + " "
            if height > 300:
                lines[-2] = lines[-2][0][:-4] + "...", lines[-2][1]
                return lines[:-1], height
    string_dimensions = cv2.getTextSize(current_line[:-1], font, 1, 2)
    lines.append((current_line[:-1], string_dimensions[0]))
    height += string_dimensions[0][1] + 15
    if height > 300:
        lines[-2] = lines[-2][0][:-4] + "...", lines[-2][1]
        return lines[:-1], height
    return lines, height


def center_text_with_ellipsis(in_string):
    string_dimensions = cv2.getTextSize(in_string, font, 1.5, 3)
    if string_dimensions[0][0] < 460:
        return in_string, string_dimensions[0]
    i = 20
    while cv2.getTextSize(in_string[:i], font, 1, 2)[0][0] < 460:
        i += 1
    out_string = in_string[:i - 3] + "..."
    return out_string, cv2.getTextSize(out_string, font, 1.5, 3)[0]


def load_animation_frame():
    gif_cap = cv2.VideoCapture(os.path.join(absolute_path, 'resources/loading.mp4'))
    loading_fps = int(1000 / gif_cap.get(cv2.CAP_PROP_FPS))
    loading_frames = []

    # Play the video once and store the frames in an array
    while gif_cap.isOpened():
        _ret, f = gif_cap.read()
        if f is None:
            break
        loading_frames.append(f)
    gif_cap.release()

    gif_cap = cv2.VideoCapture(os.path.join(absolute_path, 'resources/success.mp4'))
    success_fps = int(1000 / gif_cap.get(cv2.CAP_PROP_FPS))
    success_frames = []

    # Play the video once and store the frames in an array
    while gif_cap.isOpened():
        _ret, f = gif_cap.read()
        if f is None:
            break
        success_frames.append(f)
    gif_cap.release()

    return loading_frames, loading_fps, success_frames, success_fps


class State(Enum):
    DISCONNECTED = 0
    SCAN = 1
    SUCCESS = 2
    ERROR = 3
    LOADING = 4


class OpCode(Enum):
    CONNECT = 0
    ATTENDANCE = 1
    SUCCESSFUL = 2
    UNSUCCESSFUL = 3
    DISCONNECT = 4


class Server:
    def __init__(self):
        self.state = State.DISCONNECTED
        self.response = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread(target=self.__await_connection).start()

    def send_attendance(self, msg):
        self.__send(OpCode.ATTENDANCE, {"attendanceString": msg})
        response = self.__receive()
        if not response:
            return
        if response[0] == OpCode.SUCCESSFUL.value:
            self.response = {"Name": center_text_with_ellipsis(response[1]["Name"])}
            self.state = State.SUCCESS
        elif response[0] == OpCode.UNSUCCESSFUL.value:
            self.response = make_paragraph(response[1]["error"])
            self.state = State.ERROR
            time.sleep(2)
            self.state = State.SCAN

    def check_alive(self):
        threading.Thread(target=self.__check_connection).start()

    def set_state(self, state):
        self.state = state

    def __await_connection(self):
        self.server.settimeout(5)
        while self.server.connect_ex(ADDR) != 0:
            print("Trying to connect to server...")
            time.sleep(5)
        print("We have connected!")
        self.server.settimeout(None)
        with open(os.path.join(absolute_path, 'resources/authData.json'), 'r') as f:
            self.__send(OpCode.CONNECT, json.loads(f.read()))
            f.close()
        response = self.__receive()
        if not response:
            self.state = State.ERROR
            self.response = make_paragraph("Bad response")
            time.sleep(5)
            self.state = State.DISCONNECTED
            return
        if response[0] == OpCode.DISCONNECT.value:
            self.state = State.ERROR
            self.response = make_paragraph(response[1]["error"])
            time.sleep(5)
            self.state = State.DISCONNECTED
            return
        if response[0] == OpCode.SUCCESSFUL.value:
            self.state = State.SCAN

    def __check_connection(self):
        while True:
            s = socket.socket()
            try:
                s.connect(ADDR)
            except Exception:
                self.state = State.DISCONNECTED
                break
            finally:
                s.close()
            time.sleep(15)

    def __send(self, opcode, out_json=None):
        if out_json is None:
            out_json = {}
        json_string = json.dumps(out_json)
        msg = json_string.encode(FORMAT)
        msg_length = len(msg)
        try:
            self.server.send(opcode.value.to_bytes(length=OPCODE, byteorder=sys.byteorder, signed=False))
            self.server.send(msg_length.to_bytes(length=HEADER, byteorder=sys.byteorder, signed=False))
            self.server.send(msg)
        except Exception as e:
            self.state = State.ERROR
            self.response = make_paragraph(str(e))
            time.sleep(5)
            self.state = State.DISCONNECTED

    def __receive(self):
        opcode = self.server.recv(OPCODE)
        if opcode:
            opcode = int.from_bytes(opcode, sys.byteorder)
        msg_length = self.server.recv(HEADER)
        if msg_length:
            msg_length = int.from_bytes(msg_length, sys.byteorder)
            return opcode, json.loads(self.server.recv(msg_length).decode(FORMAT))


def main():
    server = Server()
    loading_frames, loading_fps, success_frames, success_fps = load_animation_frame()
    cv2.namedWindow(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Makes a loading animation while waiting for connection
    while server.state == State.DISCONNECTED:
        for frame in loading_frames:
            cv2.imshow(CAMERA_VIEW, frame)
            cv2.waitKey(loading_fps)

    if server.state == State.SCAN:
        server.check_alive()
    cap = cv2.VideoCapture(0)

    # Matches state to show frame
    while server.state != State.DISCONNECTED:
        success, frame = cap.read()

        # Flip and resize the camera image
        frame = cv2.flip(frame, flipCode=1)
        frame = cv2.resize(frame, (480, 320))

        if server.state == State.SCAN:
            for barcode in bar.decode(frame):
                my_data = barcode.data.decode('utf-8')
                if my_data is not None:
                    server.set_state(State.LOADING)
                    threading.Thread(target=server.send_attendance, args=(my_data,)).start()
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.LOADING:
            frame = np.full([320, 480, 3], (255, 255, 255), dtype=np.uint8)
            cv2.putText(frame, "Loading", (120, 160), font, 2, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.SUCCESS:
            for frame in success_frames:
                cv2.putText(frame, server.response["Name"][0], (int(240 - server.response["Name"][1][0] / 2), 280),
                            font, 1.5, (80, 80, 80), 3, cv2.LINE_AA)
                cv2.imshow(CAMERA_VIEW, frame)
                cv2.waitKey(int(success_fps))
            server.set_state(State.SCAN)
        elif server.state == State.ERROR:
            frame = np.full([400, 400, 3], 1, dtype=np.uint8)
            height = int(160 - server.response[1] / 2)
            for error_line in server.response[0]:
                cv2.putText(frame, error_line[0], (int(240 - error_line[1][0] / 2), height),
                            font, 1, (0, 0, 255), 2, cv2.LINE_AA)
                height += error_line[1][1] + 15
            cv2.imshow(CAMERA_VIEW, frame)
        else:
            cv2.imshow(CAMERA_VIEW, frame)
        cv2.waitKey(1)
    cap.release()
    server.server.close()
    os.system('shutdown now')


if __name__ == "__main__":
    main()
