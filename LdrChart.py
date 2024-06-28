import paho.mqtt.client as mqtt
from collections import deque
from matplotlib import pyplot as plt

mqtt_server = '192.168.1.152'
mqtt_topic = 'ldrSensor'

class LDRData:
    def __init__(self, max_data=1000):
        self.axis_x = deque(maxlen=max_data)
        self.axis_ldr = deque(maxlen=max_data)

    def add(self, x, ldr_value):
        self.axis_x.append(x)
        self.axis_ldr.append(ldr_value)

class LDRPlot:
    def __init__(self, axes):
        self.axes = axes
        self.lineplot, = axes.plot([], [], "bo--", label="LDR Value")
        self.axes.legend()
    
    def plot(self, data):
        self.lineplot.set_data(data.axis_x, data.axis_ldr)
        self.axes.set_xlim(min(data.axis_x), max(data.axis_x))
        ymin = min(data.axis_ldr) - 5
        ymax = max(data.axis_ldr) + 5
        self.axes.set_ylim(ymin, ymax)
        self.axes.figure.canvas.draw()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(mqtt_topic)

def on_message(client, userdata, msg):
    global data, myplot
    print(f"{msg.topic}: {msg.payload.decode()}")
    ldr_value = float(msg.payload.decode())
    data.add(len(data.axis_x), ldr_value)
    myplot.plot(data)

if __name__ == "__main__":
    data = LDRData()
    fig, ax = plt.subplots()
    plt.title("LDR Sensor Values")
    myplot = LDRPlot(ax)
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_server, 1883, 60)
    client.loop_start()

    while True:
        plt.pause(0.25)
