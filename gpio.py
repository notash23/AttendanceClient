import OPi.GPIO as GPIO


def thread1(button):
    print("button1")


GPIO.setmode(GPIO.SUNXI)
buttons = ["PC8"]
GPIO.setup(buttons, GPIO.IN, GPIO.HIGH)
print("waiting")
GPIO.add_event_detect(buttons[0], trigger=GPIO.FALLING, callback=thread1)
try:
    while True:
        pass # your code

except KeyboardInterrupt:
    pass
finally:
    print("\nRelease the used pin(s)")
    GPIO.cleanup()
