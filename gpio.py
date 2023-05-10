import OPi.GPIO as GPIO

GPIO.setmode(GPIO.SUNXI)
GPIO.setup("PC8", GPIO.IN, GPIO.HIGH)

GPIO.wait_for_edge("PC8", GPIO.FALLING)
print("falling")
