'''
Projet  : FESPNOW
Auteur : FredThx
'''

import time, json
import network
from esp import espnow
from FESPNOW.mqtt_pass import MqttPasse
from FESPNOW.en_mqtt_proto import ENMqttProto

class ENClient(ENMqttProto):
    '''Un client de ENServer (passerelle ESP-NOW)
    '''

    def __init__(self, esp_ssid = "ESP-NOW", timeout = 15, callback = None, timer_duration = 30, mqtt_base_topic = "ESP-NOW"):
        '''
        esp_ssid        :   SSID pour apareiller ESP-NOW (obtenir la mac du server)
        timeout         :   pour première connection ESP-NOW
        callback        :   callback for all messages
        timer_duration  :   duration (seconds) for reconnection ESP-NOW (quand en mode WIFI)
        '''
        self.discret = False
        self.esp_ssid = esp_ssid
        self.timeout = timeout
        self.wifi = {}
        self.mqtt_base_topic = mqtt_base_topic
        self.wmqtt = None
        self.wan = network.WLAN(network.STA_IF)
        self.wan.active(True)
        self.init_esp_now()
        self.esp_server = None
        self.callback = callback
        self.callbacks = {} #{topic:callback, ...}
        self.load_config()
        if self.wifi.get("ssid"):
            self.wmqtt = MqttPasse(**(self.wifi),clientName=str(self.wan.config('mac')))
        self.mqtt = None # Soit self.wmqtt (en wifi), soit self(en mode esp-now)
        self.timer_duration = timer_duration
        self.connect()

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.config(on_recv = self.on_receive)
        self.e.init()

    def save_config(self):
        data = {prop : getattr(self, prop) for prop in ['esp_server', 'wifi']}
        with open("config.json", 'w') as file:
            file.write(json.dumps(data))

    def load_config(self):
        try:
            with open("config.json", 'r') as file:
                data = json.loads(file.read())
            for prop, value in data.items():
                if type(value) == str:
                    setattr(self, prop, bytes(value,""))
                else:
                    setattr(self, prop, value)
        except Exception as e:
            self.logging(e)
        else:
            self.logging(f"load config ok. server : {self.esp_server}")
    
    def connect(self, timeout = None, discret = False):
        '''Try by esp-now with self.esp_server host
        if failed, try with WIFI with esp_ssid AP
        if failed, try with real WIFI
        '''
        if not timeout:
            timeout = self.timeout
        old_value = self.discret
        if discret:
            self.discret = True
        if not self.connect_en(timeout):
            self.logging(f"esp-now {self.esp_server} unreachable.\nTry found new server with WIFI HOTSPOT {self.esp_ssid}...")
            if not self.scan():
                self.logging(f"{self.esp_ssid} unreachable.")
                return self.connect_wifi()
        else:
            self.logging(f"Connected on ESP-NOW network. Server : {self.esp_server}")
        self.save_config()
        self.discret = old_value

    def connect_en(self, timeout = 15, discret = False):
        '''Connect to the esp-now server
        if error return False
        '''
        if timeout:
            self.logging(f"try ESP-NOW connection to {self.esp_server}", end = '')
        self.test = b"PENDING"
        _timeout = time.time()+timeout+0.1
        while time.time()<_timeout and self.test != b"OK":
            try:
                test = self.e.send(self.esp_server, self.TYPE_TEST)
            except Exception as e:
                test = False
            self.logging('.', end = '')
            time.sleep(1)#Attente retour du message
        if self.test == b"OK":
            self.logging("Connection successful")
            self.mqtt=self
            if self.wmqtt:
                self.wmqtt.disconnect()
            #refaire les subcriptions
            self.resubscribe_all()
            return True
        else:
            if timeout:
                self.logging("Connection Error : timeout")


    def scan(self):
        '''Scan for WIFI AP
        '''
        self.logging(f"Scan for {self.esp_ssid}...")
        for ssid, bssid, channel, RSSI, authmode, hidden in self.wan.scan():
            #self.logging(f"{ssid.decode()} found. RSSI = {RSSI}")
            if ssid.decode() == self.esp_ssid:
                self.logging(f"Try to connect to {ssid.decode()}...")
                self.wan.connect(ssid)
                timeout = time.time() + self.timeout
                while self.wan.status() in [network.STAT_CONNECTING, network.STAT_IDLE] and time.time()< timeout:
                    time.sleep(1)
                if self.wan.status() == network.STAT_GOT_IP:
                    self.logging("Connection successful")
                    self.esp_server = bssid
                    return self.connect_en()
                else:
                    if time.time()>timeout:
                        self.logging("Connection error : timeout")
                    else:
                        self.logging(f"Connection error. status = {self.wan.status()}")

    def connect_wifi(self):
        '''Quand aucun reseau esp-non n'est accessible => WIFI
        '''
        if self.wmqtt:
            if self.wmqtt.connect():
                self.wmqtt.callback = self.on_mqtt_message
                self.mqtt=self.wmqtt
                #refaire les subcriptions
                self.resubscribe_all()
                return True
        else:
            self.logging("No wifi configuration found. Please connect once with ESP-NOW network.")


    def resubscribe_all(self):
        '''Re-crée les subsciptions auprès du broker
        (dasn le cas où l'on change de mode)
        '''
        for topic, callback in self.callbacks.items():
            self.mqtt.subscribe(topic) #pas nécessaire de repasser la callback qui est déjà enregistrée

    def on_mqtt_message(self, topic, payload):
        '''on receive mqtt message
        (soit directement, soit suite on_receive message)
        '''
        self.logging(f"Reception de {topic}=>{payload}")
        if self.callback:
            self.callback(topic, payload)
        if topic in self.callbacks:
            self.callbacks[topic](topic, payload)

    def on_receive(self, e):
        '''On receive esp-now message
        '''
        host, msg = e.irecv() 
        msg = bytes(msg)
        self.logging(f"Reception de {msg} from {host}")
        type = msg[0]
        if type == self.TYPE_MESSAGE[0]:
            topic = msg[2:2+msg[1]]
            payload = msg[2+msg[1]:]
            self.on_mqtt_message(topic, payload)
        elif type == self.TYPE_TEST[0]:
            self.test = msg[1:]
        elif type == self.TYPE_SSID[0]:
            self.wifi['ssid'] = msg[1:]
        elif type == self.TYPE_PASSW[0]:
            self.wifi['passw'] = msg[1:]
        elif type == self.TYPE_HOST[0]:
            self.wifi['host'] = msg[1:]
        else:
            self.logging(f"oups ! message type unexpected : {type}")
            
    def send(self, data):
        if not self.e.send(self.esp_server, data):
            self.logging("Error sending data to server.")
        else:
            return True

    def get_topic(self, topic:str)-> str:
        '''Ajout base_topic quand './' devant
        '''
        if self.mqtt_base_topic and topic[:2]=="./":
            return self.mqtt_base_topic + topic[1:]
        else:
            return topic

    def publish(self, topic, payload, trys = 0):
        '''publish msg to mqtt broker via esp-now
        '''
        topic = self.get_topic(topic)
        payload = payload or ""
        if trys >1:
            return False
        else:
            if self.mqtt == self:#Mode ESP-NOW
                assert len(topic)+len(payload)< 248, "Message too long!"
                data = self.TYPE_PUBLISH+chr(len(topic))+topic+payload
                if not self.send(data):
                    if self.connect():
                        self.publish(topic, payload, trys+1)
            elif self.mqtt == self.wmqtt:#Mode WIFI
                self.wmqtt.publish(topic, payload)

    def subscribe(self, topic, callback = None):
        '''Subscibe to a mqtt topic via esp-now
        '''
        topic = self.get_topic(topic)
        if self.mqtt == self: #Mode ESP-NOW
            assert len(topic)< 248, "topic too long!"
            data = self.TYPE_SUBSCRIBE+topic
            self.send(data)
        elif self.mqtt== self.wmqtt: #Mode WIFI
            self.wmqtt.subscribe(topic)
        else:
            self.logging("Oups, nos connection available!")
            return False
        if callback:
            self.callbacks[bytes(topic,'utf-8')]=callback

    def logging(self, txt, end = '\n'):
        if not self.discret:
            print(txt,end=end)

class ENClient8266(ENClient):
    '''une passerelle ESP-NOW 8266
    '''

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.init(None, None, self.on_receive)