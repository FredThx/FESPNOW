'''
Projet  : FESPNOW
Auteur : FredThx
Version : utilisée pour Olfa
'''


import time
from machine import Timer
import network
from .umqtt.simple import MQTTClient


class MqttPasse:
    '''une passerelle vers mqtt via un reseau WIFI
    '''
    def __init__(self, ssid, passw, host, clientName = "ESP-NOW", timeout = 15, callback = None, autoconnect = False):
        self.ssid = ssid
        self.passw = passw
        self.host = host
        self.timeout = timeout
        self.callback = callback
        self.wan = network.WLAN(network.STA_IF) #STATION        
        self.mqtt = MQTTClient(clientName, host)
        self.mqtt.set_callback(self.on_mqtt_message)
        self.timer = Timer(-1)
        if autoconnect:
            self.connect()

    def connect(self):
        if self.wifi_connect():
            try:
                self.mqtt.connect()
            except OSError:
                return False
            else:
                self.timer.init(mode = Timer.PERIODIC, period = 200, callback = lambda tim:self.mqtt.check_msg())
                return True

    def wifi_connect(self):
        self.wan.active(True)
        self.wan.connect(self.ssid,self.passw)
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
        esp_now.mqtt = self
        #WIFI-MQTT- => ESP-MQTT
        self.callback = esp_now.on_mqtt_incoming
        #ESP-NOW => WIFI-MQTT
        esp_now.mqtt_publish = self.publish
        esp_now.mqtt_subscribe = self.subscribe

    def loop_forever(self):#OBSOLETE
        print("Loop ... forever")
        while True:
            self.mqtt.wait_msg()
    
    def loop(self, wait = True):#OBSOLETE
        if wait:
            print("Wait for mqtt message ...")
            self.mqtt.wait_msg()
        else:
            self.mqtt.check_msg()
    
    def disconnect(self):#OBSOLETE
        try:
            self.mqtt.disconnect()
            self.timer.deinit()
        except:
            pass
        self.wan.disconnect()
        self.wan.active(True)