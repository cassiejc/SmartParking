import network
import time
from umqtt.simple import MQTTClient
import machine
from machine import I2C, Pin, PWM
import ssd1306

# Replace with your network credentials
SSID = '.'
PASSWORD = 'cassiejc'

# MQTT broker details
MQTT_BROKER = 'broker.emqx.io'
CLIENT_ID = 'esp8266_client'

# Topics for sensors
MQTT_MQ5_TOPIC = 'mq5Sensor'
MQTT_IR_TOPIC1 = 'irSensor1'  # Topic for IR sensor on D2
MQTT_IR_TOPIC2 = 'irSensor2'  # Topic for IR sensor on D3
MQTT_IR_TOPIC3 = 'irSensor3'  # Topic for IR sensor on D4
MQTT_OLED_TOPIC = 'oledDisplay'  # Topic for OLED display status
MQTT_TOTAL_CARS_TOPIC = 'totalCars'  # Topic for total cars detected

# Setup the MQ-5 sensor pin (Assuming A0 for analog input)
mq5_sensor = machine.ADC(0)

# Setup the IR sensor digital input pins
ir_sensor_pin_d2 = machine.Pin(4, machine.Pin.IN)  # D2 corresponds to GPIO 4 on ESP8266
ir_sensor_pin_d3 = machine.Pin(0, machine.Pin.IN)  # D3 corresponds to GPIO 0 on ESP8266
ir_sensor_pin_d4 = machine.Pin(2, machine.Pin.IN)  # D4 corresponds to GPIO 2 on ESP8266

# Setup the SSD1306 display (SCL = D5 = GPIO14, SDA = D6 = GPIO12)
i2c = I2C(scl=Pin(14), sda=Pin(12))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Setup the servo motor on pin D7 (GPIO 13)
servo_pin = machine.Pin(13)
servo = PWM(servo_pin, freq=50)

# Function to set the servo angle
def set_servo_angle(angle):
    duty = int((angle / 180.0 * 1023.0) + 25.6)  # Calculate duty cycle
    servo.duty(duty)

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        pass
    print('Connection successful')
    print(wlan.ifconfig())

# Publish message to MQTT
def publish_message(client, topic, message):
    client.publish(topic, message)

# Main function
def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883)
    client.connect()
    
    try:
        while True:
            # Read the analog value from the MQ-5 sensor
            mq5_value = mq5_sensor.read()
            publish_message(client, MQTT_MQ5_TOPIC, str(mq5_value))
            
            # Read the digital state of the IR sensor pins
            ir_value_d2 = ir_sensor_pin_d2.value()  # 0 if LOW, 1 if HIGH
            ir_value_d3 = ir_sensor_pin_d3.value()  # 0 if LOW, 1 if HIGH
            ir_value_d4 = ir_sensor_pin_d4.value()  # 0 if LOW, 1 if HIGH
            
            # Publish MQTT messages for IR sensor on D2
            if ir_value_d2 == 0:
                publish_message(client, MQTT_IR_TOPIC1, 'Car Detected')
            else:
                publish_message(client, MQTT_IR_TOPIC1, 'No Car')
            
            # Publish MQTT messages for IR sensor on D3
            if ir_value_d3 == 0:
                publish_message(client, MQTT_IR_TOPIC2, 'Car Detected')
            else:
                publish_message(client, MQTT_IR_TOPIC2, 'No Car')

            # Publish MQTT messages for IR sensor on D4
            if ir_value_d4 == 0:
                publish_message(client, MQTT_IR_TOPIC3, 'Car Detected')
            else:
                publish_message(client, MQTT_IR_TOPIC3, 'No Car')
                
            # Determine car presence status and OLED display text
            if ir_value_d2 == 0 and ir_value_d3 == 0 and ir_value_d4 == 0:
                oled.fill(0)
                oled.text("FULL!!!", 48, 28)  # Center the text
                oled.show()
                set_servo_angle(0)  # Close the gate
                display_status = "FULL"
            else:
                oled.fill(0)
                oled.text("AVAILABLE", 28, 28)  # Center the text
                oled.show()
                set_servo_angle(90)  # Open the gate
                display_status = "AVAILABLE"
            
            # Publish MQTT message for OLED display status
            publish_message(client, MQTT_OLED_TOPIC, display_status)
            
            # Publish MQTT message for display MQTT topics
            if display_status == "FULL":
                publish_message(client, MQTT_TOTAL_CARS_TOPIC, "FULL!!!")
            else:
                publish_message(client, MQTT_TOTAL_CARS_TOPIC, "AVAILABLE")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        client.disconnect()

if __name__ == '__main__':
    main()

