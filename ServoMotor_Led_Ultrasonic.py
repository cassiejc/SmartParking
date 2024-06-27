from machine import Pin, PWM
import time
import network
import ubinascii
from umqtt.robust import MQTTClient

SSID = 'IoT_Dev'
PASSWORD = 'elektro234'

MQTT_BROKER = '192.168.1.152'
CLIENT_ID = 'mqttx_7e707bae'
TOPIC_OLEDDISPLAY = 'oledDisplay'
TOPIC_LDRSENSOR = 'ldrSensor'  

oled_state = ""
ldr_value = 0

def sub_cb(topic, msg):
    global oled_state, ldr_value
    if topic == b'oledDisplay':
        oled_state = msg.decode('utf-8')
    elif topic == b'ldrSensor':
        ldr_value = int(msg.decode('utf-8'))
        control_led(ldr_value)

def control_led(value):
    if value < 350:
        led.off()
        print("LED OFF")
    else:
        led.on()
        print("LED ON")

def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(SSID, PASSWORD)
    while not wifi.isconnected():
        time.sleep(1)
    print('Wi-Fi connected, IP:', wifi.ifconfig()[0])

servo_pin = Pin(14, Pin.OUT)  
servo = PWM(servo_pin, freq=50)

led = Pin(15, Pin.OUT)  

trigger_pin = Pin(5, Pin.OUT)  
echo_pin = Pin(4, Pin.IN)     

def move_servo(angle):
    duty = int((angle / 180) * 1024 / 20 + 26)  
    servo.duty(duty)

def measure_distance():
    trigger_pin.off()
    time.sleep_us(1)
    trigger_pin.on()
    time.sleep_us(5)
    trigger_pin.off()

    timeout_start = time.ticks_us()
    while echo_pin.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout_start) > 1000:  
            print("Timeout waiting for echo start")
            return None
    start_time = time.ticks_us()
    
    timeout_start = time.ticks_us()
    while echo_pin.value() == 1:
        if time.ticks_diff(time.ticks_us(), timeout_start) > 1000:  
            print("Timeout waiting for echo end")
            return None
    end_time = time.ticks_us()
    
    pulse_duration = time.ticks_diff(end_time, start_time)
    distance = (pulse_duration * 0.0343) / 2  
    return distance

def control_gate():
    global oled_state
    if oled_state == "AVAILABLE":
        distance = measure_distance()
        if distance is not None:
            print("Distance: {:.2f} cm".format(distance))
            if distance < 15:  
                print("Object detected! Opening gate...")
                move_servo(90)  
            else:
                print("No object detected. Closing gate...")
                move_servo(0)  
        else:
            print("Failed to measure distance")
    elif oled_state == "FULL":
        print("Gate locked. No action needed.")
        move_servo(0)  

connect_wifi()
client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(sub_cb)
client.connect()
client.subscribe(TOPIC_OLEDDISPLAY)
client.subscribe(TOPIC_LDRSENSOR)  

try:
    while True:
        client.check_msg()  
        control_gate()  
        time.sleep(1)  
except KeyboardInterrupt:
    print("Program stopped")

client.disconnect()
