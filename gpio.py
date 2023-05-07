from time import sleep

import OPi.GPIO as GPIO


GPIO.setmode(GPIO.BOARD)
button1 = 8

GPIO.setup(button1, GPIO.IN)

while True:
    if GPIO.input(button1):
        print("Button 1 has been pressed")
    sleep(1)