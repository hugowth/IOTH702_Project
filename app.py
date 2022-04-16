import time
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import paho.mqtt.client as mqtt
from constants import (
    MQTT_HOST,
    INTERVAL,
)

f = PiGPIOFactory("127.0.0.1")
servo = Servo(27, pin_factory=f)
next_reading = time.time()
servo.min()  # Initialization
time.sleep(2)


def control_servo(action):
    if action == "b'lock'" and servo.value != 1.0:
        servo.max()
    if action == "b'unlock'" and servo.value != -1.0:
        servo.min()
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


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883, 60)
client.loop_start()

while True:
    value = "lock" if servo.value == 1.0 else "unlock"
    client.publish(
        "servo/status",
        value,
        1,
    )
    next_reading += INTERVAL
    sleep_time = next_reading - time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)
