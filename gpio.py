import OPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
button1 = 15

GPIO.setup(button1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    if GPIO.input(button1):
        print("Button 1 has been pressed")
