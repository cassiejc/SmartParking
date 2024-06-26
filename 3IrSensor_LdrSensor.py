import network
import time
from umqtt.simple import MQTTClient
import machine
from machine import I2C, Pin, PWM
import ssd1306

SSID = 'IoT_Dev'
PASSWORD = 'elektro234'

MQTT_BROKER = '192.168.1.152'
CLIENT_ID = 'esp8266_client'

MQTT_LDR_TOPIC = 'ldrSensor'
MQTT_IR_TOPIC1 = 'irSensor1'  
MQTT_IR_TOPIC2 = 'irSensor2'  
MQTT_IR_TOPIC3 = 'irSensor3'  
MQTT_OLED_TOPIC = 'oledDisplay'  
MQTT_TOTAL_CARS_TOPIC = 'totalCars'  

ldr_sensor = machine.ADC(0)

ir_sensor_pin_d2 = machine.Pin(4, machine.Pin.IN)  
ir_sensor_pin_d3 = machine.Pin(0, machine.Pin.IN)  
ir_sensor_pin_d4 = machine.Pin(2, machine.Pin.IN)  

i2c = I2C(scl=Pin(14), sda=Pin(12))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

servo_pin = machine.Pin(13)
servo = PWM(servo_pin, freq=50)

def set_servo_angle(angle):
    duty = int((angle / 180.0 * 1023.0) + 25.6)  
    servo.duty(duty)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        pass
    print('Connection successful')
    print(wlan.ifconfig())

def publish_message(client, topic, message):
    client.publish(topic, message)

def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883)
    client.connect()
    
    try:
        while True:
            # Read the analog value from the LDR sensor
            ldr_value = ldr_sensor.read()
            publish_message(client, MQTT_LDR_TOPIC, str(ldr_value))
            
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

