from time import sleep
import sys
import OPi.GPIO as GPIO


GPIO.setmode(GPIO.BOARD)
button = int(sys.argv[1])

GPIO.setup(button, GPIO.IN)

while True:
    GPIO.wait_for_edge(button, GPIO.BOTH)
    print("State of this button changed")
    sleep(1)
GPIO.cleanup()
