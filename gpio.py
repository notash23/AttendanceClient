import OPi.GPIO as GPIO

GPIO.setmode(GPIO.SUNXI)
buttons = ["PC8", "PC11"]
GPIO.setup(buttons, GPIO.IN, GPIO.HIGH)
print("waiting")
GPIO.wait_for_edge(buttons[0], GPIO.FALLING)
print("falling")
GPIO.wait_for_edge(buttons[0], GPIO.FALLING)
print("falling again")
GPIO.cleanup()
