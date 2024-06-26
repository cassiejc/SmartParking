from machine import Pin, PWM
import time
import network
import ubinascii
from umqtt.robust import MQTTClient

# Wi-Fi configuration
SSID = 'IoT_Dev'
PASSWORD = 'elektro234'

# MQTT configuration
MQTT_BROKER = '192.168.1.152'
CLIENT_ID = 'mqttx_7e707bae'
TOPIC_OLEDDISPLAY = 'oledDisplay'
TOPIC_LDRSENSOR = 'ldrSensor'
TOPIC_GATECOUNT = 'gateCount'  # New topic for gate count

# Global variables
oled_state = ""
ldr_value = 0
gate_count = 0  # Counter for gate openings
object_detected = False  # State to track if object is detected

# Function to handle received messages
def sub_cb(topic, msg):
    global oled_state, ldr_value
    print(f"Message received: {topic} -> {msg}")
    if topic == b'oledDisplay':
        oled_state = msg.decode('utf-8')
    elif topic == b'ldrSensor':
        ldr_value = int(msg.decode('utf-8'))
        control_led(ldr_value)

# Function to control LED based on LDR value
def control_led(value):
    if value < 350:
        led.off()
        print("LED OFF")
    else:
        led.on()
        print("LED ON")

# Setup Wi-Fi connection
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(SSID, PASSWORD)
    while not wifi.isconnected():
        time.sleep(1)
        print("Connecting to Wi-Fi...")
    print('Wi-Fi connected, IP:', wifi.ifconfig()[0])

# Define pin for servo motor
servo_pin = Pin(14, Pin.OUT)  # D5 GPIO14
servo = PWM(servo_pin, freq=50)

# Define pin for LED
led = Pin(15, Pin.OUT)  # D8 GPIO2

# Define pins for ultrasonic sensor
trigger_pin = Pin(5, Pin.OUT)  # D1 GPIO5
echo_pin = Pin(4, Pin.IN)      # D2 GPIO4

# Function to move servo to a specified angle
def move_servo(angle):
    duty = int((angle / 180) * 1024 / 20 + 26)  # Convert angle to duty cycle
    servo.duty(duty)
    print(f"Servo moved to {angle} degrees")

# Function to measure distance using ultrasonic sensor
def measure_distance():
    # Trigger the ultrasonic burst
    trigger_pin.off()
    time.sleep_us(1)
    trigger_pin.on()
    time.sleep_us(5)
    trigger_pin.off()

    # Measure the duration of the echo pulse
    timeout_start = time.ticks_us()
    while echo_pin.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout_start) > 1000:  # 1ms timeout
            print("Timeout waiting for echo start")
            return None
    start_time = time.ticks_us()
    
    timeout_start = time.ticks_us()
    while echo_pin.value() == 1:
        if time.ticks_diff(time.ticks_us(), timeout_start) > 1000:  # 1ms timeout
            print("Timeout waiting for echo end")
            return None
    end_time = time.ticks_us()
    
    pulse_duration = time.ticks_diff(end_time, start_time)
    distance = (pulse_duration * 0.0343) / 2  # Convert to cm
    return distance

# Main logic for opening/closing gate based on sensor states and oled state
def control_gate():
    global oled_state, gate_count, object_detected
    print(f"OLED State: {oled_state}")
    if oled_state == "AVAILABLE":
        distance = measure_distance()
        if distance is not None:
            print("Distance: {:.2f} cm".format(distance))
            if distance < 10 and not object_detected:  # Object detected and was not previously detected
                print("Object detected! Opening gate...")
                move_servo(90)  # Open gate (adjust angle as needed)
                object_detected = True  # Set object detected state to True
            elif distance >= 10 and object_detected:  # Object has moved away
                print("Object has passed. Closing gate...")
                move_servo(0)  # Close gate (adjust angle as needed)
                gate_count += 1
                print(f"Gate count: {gate_count}")
                client.publish(TOPIC_GATECOUNT, str(gate_count))  # Publish gate count
                object_detected = False  # Reset object detected state
            else:
                print("Object still present. Waiting...")
        else:
            print("Failed to measure distance")
    elif oled_state == "FULL":
        print("Gate locked. No action needed.")
        move_servo(0)  # Ensure servo is at closed position

# Setup Wi-Fi and MQTT connection
connect_wifi()
client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(sub_cb)
client.connect()
client.subscribe(TOPIC_OLEDDISPLAY)
client.subscribe(TOPIC_LDRSENSOR)  # Subscribe to the new LDR sensor topic

print("Connected to MQTT broker and subscribed to topics")

# Main loop
try:
    while True:
        client.check_msg()  # Check for new messages
        control_gate()  # Control gate based on oled display state
        time.sleep(1)  # Wait for 1 second before checking again
except KeyboardInterrupt:
    print("Program stopped")

client.disconnect()
