import OPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
button1 = 12
button2 = 15

GPIO.setmode(button1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setmode(button1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    if GPIO.input(button1):
        print("Button 1 has been pressed")
    elif GPIO.input(button2):
        print("Button 2 has been pressed")
