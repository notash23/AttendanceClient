import OPi.GPIO as GPIO


def thread1():
    print("button1")


def thread2():
    print("button2")


GPIO.setmode(GPIO.SUNXI)
buttons = ["PC8", "PC11"]
GPIO.setup(buttons, GPIO.IN, GPIO.HIGH)
print("waiting")
GPIO.add_event_detect(buttons[0], trigger=GPIO.FALLING, callback=thread1)
GPIO.add_event_detect(buttons[1], trigger=GPIO.FALLING, callback=thread2)
GPIO.cleanup()
