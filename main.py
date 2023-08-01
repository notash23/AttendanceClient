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

SERVER = "192.168.100.165"
PORT = 5050
ADDR = (SERVER, PORT)
HEADER = 4
OPCODE = 1
FORMAT = 'utf-8'
CAMERA_VIEW = 'CameraView'
font = cv2.FONT_HERSHEY_SIMPLEX


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
    string_dimensions = cv2.getTextSize(in_string, font, 1, 1)
    if string_dimensions[0][0] < 460:
        return [(in_string, string_dimensions[0])], string_dimensions[0][1]
    words = in_string.split()
    lines = []
    current_line = ""
    height = 0
    for word in words:
        current_line_dimension = cv2.getTextSize(current_line + word + " ", font, 1, 1)
        if current_line_dimension[0][0] < 460:
            current_line += word + " "
        else:
            string_dimensions = cv2.getTextSize(current_line[:-1], font, 1, 1)
            lines.append((current_line[:-1], string_dimensions[0]))
            height += string_dimensions[0][1] + 15
            current_line = word + " "
            if height > 300:
                lines[-2] = lines[-2][0][:-4] + "...", lines[-2][1]
                return lines[:-1], height
    string_dimensions = cv2.getTextSize(current_line[:-1], font, 1, 1)
    lines.append((current_line[:-1], string_dimensions[0]))
    height += string_dimensions[0][1] + 15
    if height > 300:
        lines[-2] = lines[-2][0][:-4] + "...", lines[-2][1]
        return lines[:-1], height
    return lines, height


def center_text_with_ellipsis(in_string):
    string_dimensions = cv2.getTextSize(in_string, font, 1, 2)
    if string_dimensions[0][0] < 460:
        return in_string, string_dimensions[0]
    i = 20
    while cv2.getTextSize(in_string[:i], font, 1, 2)[0][0] < 460:
        i += 1
    print(in_string[:i])
    out_string = in_string[:i - 3] + "..."
    return out_string, cv2.getTextSize(out_string, font, 1, 2)[0]


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


class ButtonCode(Enum):
    YES = "PC8"
    NO = "PC11"


class Server:
    def __init__(self):
        self.state = State.DISCONNECTED
        self.response = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread(target=self.await_connection).start()

    def await_connection(self):
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
            self.response = make_paragraph(response[1]["error"])
            self.server.close()
            time.sleep(2)
            self.state = State.DISCONNECTED
            return
        if response[0] == OpCode.SUCCESSFUL.value:
            self.state = State.SCAN

    def shutdown(self):
        self.__send(OpCode.DISCONNECT)
        self.state = State.SHUT_DOWN

    def set_loading(self):
        self.state = State.LOADING

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
        elif response[0] == OpCode.STAFF_ATTENDANCE.value:
            formatted_dict = {}
            for key, value in response[1].items():
                formatted_dict[key] = center_text_with_ellipsis(value)
            self.response = formatted_dict
            self.state = State.STAFF_SELECT

    def respond_staff_leave(self, button):
        print(button)
        if self.state != State.STAFF_SELECT:
            return
        self.state = State.LOADING
        if button == ButtonCode.YES.value:
            self.__send(OpCode.STAFF_ATTENDANCE, {"setLeave": "yes"})
            response = self.__receive()
            if not response:
                return
            if response[0] == OpCode.SUCCESSFUL.value:
                self.response = response[1]
                self.state = State.SUCCESS
            elif response[0] == OpCode.UNSUCCESSFUL.value:
                self.response = make_paragraph(response[1]["error"])
                self.state = State.ERROR
                time.sleep(2)
                self.state = State.SCAN
        elif button == ButtonCode.NO.value:
            self.__send(OpCode.STAFF_ATTENDANCE)

    def set_state(self, state):
        self.state = state

    def __send(self, opcode, out_json=None):
        if out_json is None:
            out_json = {}
        json_string = json.dumps(out_json)
        msg = json_string.encode(FORMAT)
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
    gif_cap = cv2.VideoCapture(r'resources/nyan-cat.mp4')
    nyan_fps = 1000 / gif_cap.get(cv2.CAP_PROP_FPS)
    nyan_frames = []

    # Play the video once and store the frames in an array
    while gif_cap.isOpened():
        _ret, f = gif_cap.read()
        if f is None:
            break
        nyan_frames.append(cv2.resize(f, (480, 320)))
    gif_cap.release()

    gif_cap = cv2.VideoCapture(r'resources/borat-nice.mp4')
    borat_fps = 1000 / gif_cap.get(cv2.CAP_PROP_FPS)
    borat_frames = []

    # Play the video once and store the frames in an array
    while gif_cap.isOpened():
        _ret, f = gif_cap.read()
        if f is None:
            break
        borat_frames.append(cv2.resize(f, (480, 320)))
    gif_cap.release()

    cv2.namedWindow(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(CAMERA_VIEW, cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)

    server = Server()
    GPIO.setmode(GPIO.SUNXI)
    buttons = [ButtonCode.YES.value, ButtonCode.NO.value]
    GPIO.setup(buttons, GPIO.IN, GPIO.HIGH)
    GPIO.add_event_detect(buttons[0], trigger=GPIO.FALLING, callback=server.respond_staff_leave)
    GPIO.add_event_detect(buttons[1], trigger=GPIO.FALLING, callback=server.respond_staff_leave)

    # Makes a loading animation while waiting for connection
    dots = '.'
    index = 0
    while server.state == State.DISCONNECTED:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        if index == len(nyan_frames) - 1:
            index = 0
        else:
            index += 1

        if len(dots) > 3:
            dots = '.'
        else:
            dots += '.'
        frame = cv2.putText(nyan_frames[index], f"Connecting{dots}", (45, 165), font, 2, (255, 255, 255), 5,
                            cv2.LINE_AA)
        cv2.imshow(CAMERA_VIEW, frame)
        cv2.waitKey(int(nyan_fps))

    cap = cv2.VideoCapture(0)

    # Matches state to show frame
    while server.state != State.DISCONNECTED:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        success, frame = cap.read()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        if server.state == State.SCAN:
            if cap.isOpened():
                for barcode in bar.decode(frame):
                    my_data = barcode.data.decode('utf-8')
                    try:
                        if my_data is not None:
                            server.set_loading()
                            threading.Thread(target=server.send_attendance, args=(my_data,)).start()
                    except KeyboardInterrupt:
                        server.state = State.ERROR
                cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.LOADING:
            frame = np.full([320, 480, 3], (255, 255, 255), dtype=np.uint8)
            cv2.putText(frame, "Loading", (120, 160), font, 2, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.SUCCESS:
            for frame in borat_frames:
                cv2.putText(frame, server.response["Name"][0], (int(240 - server.response["Name"][1][0] / 2), 100),
                            font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow(CAMERA_VIEW, frame)
                cv2.waitKey(int(borat_fps))
            server.set_state(State.SCAN)
        elif server.state == State.STAFF_SELECT:
            threading.Thread(target=server.respond_staff_leave).start()
            frame = np.full([320, 480, 3], (255, 255, 255), dtype=np.uint8)
            cv2.putText(frame, "Are you leaving?", (104, 40), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, server.response["SIC"][0], (int(240 - server.response["SIC"][1][0] / 2),
                                                           int(100 + server.response["SIC"][1][1] / 2)), font, 1,
                        (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, server.response["Name"][0],
                        (int(240 - server.response["Name"][1][0] / 2), int(170 + server.response["Name"][1][1] / 2)),
                        font, 1, (0, 0, 0))
            cv2.putText(frame, server.response["Department"][0],
                        (int(240 - server.response["Department"][1][0] / 2), 275), font, 1, (0, 0, 0))
            cv2.imshow(CAMERA_VIEW, frame)
        elif server.state == State.ERROR:
            frame = np.full([400, 400, 3], 1, dtype=np.uint8)
            height = int(160 - server.response[1] / 2)
            for error_line in server.response[0]:
                cv2.putText(frame, error_line[0], (int(240 - error_line[1][0] / 2), height),
                            font, 1, (0, 0, 255), 2, cv2.LINE_AA)
                height += error_line[1][1] + 15
            cv2.imshow(CAMERA_VIEW, frame)
        else:
            success, frame = cap.read()
            cv2.imshow(CAMERA_VIEW, frame)
        cv2.waitKey(1)
        if cv2.getWindowProperty(CAMERA_VIEW, cv2.WND_PROP_VISIBLE) < 1:
            break
    cap.release()
    GPIO.cleanup(buttons)
    cv2.destroyAllWindows()
    server.shutdown()


if __name__ == "__main__":
    main()
