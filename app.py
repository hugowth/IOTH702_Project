import time
from gpiozero import Servo, DistanceSensor, LED, Button
from gpiozero.pins.pigpio import PiGPIOFactory
import paho.mqtt.client as mqtt
from signal import pause
from constants import (
    MQTT_HOST,
    INTERVAL,
    SERVO_PIN,
    LED_PIN,
    DISTANCE_ECHO,
    DISTANCE_TRIG,
    BUTTON_PIN
)

f = PiGPIOFactory("127.0.0.1")
servo = Servo(SERVO_PIN, pin_factory=f)
next_reading = time.time()
servo.min()  # Initialization

threshold_distance = 0
sensor = DistanceSensor(echo=DISTANCE_ECHO, trigger=DISTANCE_TRIG, pin_factory=f)
button = Button(BUTTON_PIN)
led = LED(LED_PIN)

time.sleep(2)


def control_servo(action):
    if action == "b'lock'" and servo.value != 1.0:
        servo.max()
        print("door locked")
        client.publish("servo/status", "lock", 1)
    if action == "b'unlock'" and servo.value != -1.0:
        servo.min()
        print("door unlocked")
        client.publish("servo/status", "unlock", 1)
    time.sleep(0.5)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("servo/control")


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    if msg.topic == "servo/control":
        control_servo(
            str(msg.payload),
        )
        
def door_closed():
    led.off()
    print("door closed")
    time.sleep(1) # auto lock after 1 second
    control_servo("b'lock'")
    client.publish("servo/status", "lock", 1)

def door_not_close():
    # send mqtt message
    led.blink()
    print("door not close")
    
    client.publish("servo/status", "unlock", 1)
    
def lock_switch():
    if servo.value == 1.0:
        control_servo("b'unlock'")
    else:
        control_servo("b'lock'")
    time.sleep(0.5)
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883, 60)
client.loop_start()

try:
    while threshold_distance == 0: # Initial setup
            led.blink()
            button.wait_for_press() # wait the button press after closed the door
            current = sensor.distance
            led.off()
            print("Initial setup completed")
            threshold_distance = current * 1.1 # add 10% for tolerance
            sensor.threshold_distance = threshold_distance
            sensor.when_in_range = door_closed
            sensor.when_out_of_range = door_not_close
            button.when_pressed = lock_switch
            
    pause()
#     while True:
#         value = "lock" if servo.value == 1.0 else "unlock"
#         client.publish(
#             "servo/status",
#             value,
#             1,
#         )
#         next_reading += INTERVAL
#         sleep_time = next_reading - time.time()
#         if sleep_time > 0:
#             time.sleep(sleep_time)
except KeyboardInterrupt:
    led.close()
    button.close()
    sensor.close()
    servo.close()
