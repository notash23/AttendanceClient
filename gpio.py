import OPi.GPIO as GPIO

GPIO.setmode(GPIO.SUNXI)
GPIO.setup("PC8", GPIO.IN, GPIO.HIGH)
print("waiting")
GPIO.wait_for_edge("PC8", GPIO.FALLING)
print("falling")
GPIO.cleanup()

