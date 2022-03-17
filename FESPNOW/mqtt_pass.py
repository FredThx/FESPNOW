'''
Projet  : FESPNOW
Auteur : FredThx
'''

import time
import network
from .umqtt.simple import MQTTClient


class MqttPasse:
    '''une passerelle vers mqtt via un reseau WIFI
    '''
    def __init__(self, ssid, password, host, clientName = "ESP-NOW8", timeout = 30, callback = None, base_topic = "ESP-NOW"):
        self.ssid = ssid
        self.password = password
        self.timeout = timeout
        self.callback = callback
        self.base_topic = base_topic #Inutil
        self.wan = network.WLAN(network.STA_IF) #STATION        
        self.mqtt = MQTTClient(clientName, host)
        self.mqtt.set_callback(self.on_mqtt_message)
        while not self.wifi_connect():
            pass
        self.mqtt.connect()
        

    def wifi_connect(self):
        self.wan.active(True)
        self.wan.connect(self.ssid,self.password)
        print("Connection WIFI en cours .", end="")
        timeout = time.time() + self.timeout
        while not self.wan.isconnected() and time.time() < timeout:
            print(".",end="")
            time.sleep(1)
        if self.wan.isconnected():
            print("WIFI connected.")
            return True
        else:
            self.wan.disconnect()
            self.wan.active(False)
            print("Erreur : timeout.")

    def on_mqtt_message(self, topic, msg):
        print(f"Recept MQTT : {topic} : {msg}")
        if self.callback:
            self.callback(topic, msg)

    def publish(self, topic, msg):
        '''Callback for ENServer
        '''
        print(f"publish {topic} : {msg}")
        self.mqtt.publish(topic, msg)

    def subscribe(self, topic):
        '''Subscribe to a topic at mqtt broker
        '''
        self.mqtt.subscribe(topic)

    def link(self, esp_now):
        '''Connect les deux reseaux ESP-NOW <-> WIFI-MQTT
        '''
        #WIFI-MQTT- => ESP-MQTT
        self.callback = esp_now.on_mqtt_incoming
        #ESP-NOW => WIFI-MQTT
        esp_now.mqtt_publish = self.publish
        esp_now.mqtt_subscribe = self.subscribe

    def loop_forever(self):
        print("Loop ... forever")
        while True:
            self.mqtt.wait_msg()