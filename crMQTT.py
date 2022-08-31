import json

from http import server
import paho.mqtt.client as mqtt

class crMQTT:

    def __init__(self,address,port):
        self.server_key = (address,port)
        self.mqtt_server = mqtt.Client()
        self.mqtt_server.on_connect = self.on_connect
        self.mqtt_server.on_message = self.on_message
        self.mqtt_server.connect(address,port,60)
        self.mqtt_server.loop_start()
        self.callbacks = []

    def on_connect(self,client, userdata, flags, rc):
        for cb in self.callbacks:
            self.mqtt_server.subscribe(cb)

    def on_message(self,client, userdata, message):
        m_raw = message.payload.decode("utf-8")
        m = json.loads(m_raw)
        print(f'Received <{m}> from MQTT server')

    def subscribe(self,server_key,tag,cb):
        self.callbacks.append((tag,cb))

    def publish(self,tag,message):
        self.mqtt_server.publish(tag,message)
