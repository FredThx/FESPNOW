'''
Projet  : FESPNOW
Auteur : FredThx
'''

import time, json
import machine
import network
from esp import espnow
from FESPNOW.mqtt_pass import MqttPasse
from FESPNOW.en_mqtt_proto import ENMqttProto

class ENClient(ENMqttProto):
    '''Un client de ENServer (passerelle ESP-NOW)
    '''

    def __init__(self, esp_ssid = "ESP-NOW", timeout = 15, callback = None):
        self.esp_ssid = esp_ssid
        self.timeout = timeout
        self.wifi = {}
        self.wmqtt = None
        self.wan = network.WLAN(network.STA_IF)#STATION
        self.wan.active(True)
        self.init_esp_now()
        self.server = None
        self.callback = callback
        self.callbacks = {} #{topic:callback, ...}
        self.load_config()
        if self.wifi.get("ssid"):
            self.wmqtt = MqttPasse(**(self.wifi),clientName=str(self.wan.config('mac')))
        self.status = {'mqtt' : None, 'timeout' : None}
        self.connect()
            

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.config(on_recv = self.on_receive)
        self.e.init()

    def save_config(self):
        data = {prop : getattr(self, prop) for prop in ['server', 'wifi']}
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
            print(e)
        else:
            print(f"load config ok. server : {self.server}")
    
    def connect(self):
        '''Try by esp-now with self.server host
        if failed, try with WIFI with esp_ssid AP
        if failed, try with real WIFI
        '''
        if not self.connect_en():
            print(f"esp-now {self.server} unreachable.\nTry connection on WIFI {self.esp_ssid}...")
            if not self.scan():
                print(f"{self.esp_ssid} unreachable.")
                return self.connect_wifi()
        self.save_config()

    def connect_en(self, timeout = 15):
        '''Connect to the esp-now server
        if error return False
        '''
        print(f"try ESP-NOW connection to {self.server}", end = '')
        try:
            self.e.add_peer(self.server)
        except Exception as e:
            print(e)
        self.test = b"PENDING"
        timeout = time.time()+timeout
        while time.time()<timeout and self.test != b"OK":
            try:
                self.e.send(self.server, self.TYPE_TEST)
            except Exception as e:
                print(e)
            print('.', end = '')
            time.sleep(1)
        if self.test == b"OK":
            print("Connection successful")
            self.status['mqtt']=self
            return True
        else:
            self.status['mqtt'] = None
            print("Connection Error : timeout")


    def scan(self):
        '''Scan for WIFI AP
        '''
        print(f"Scan for {self.esp_ssid}...")
        for ssid, bssid, channel, RSSI, authmode, hidden in self.wan.scan():
            print(f"{ssid.decode()} found. RSSI = {RSSI}")
            if ssid.decode() == self.esp_ssid:
                print(f"Try to connect to {ssid.decode()}...")
                self.wan.connect(ssid)
                timeout = time.time() + self.timeout
                while self.wan.status() in [network.STAT_CONNECTING, network.STAT_IDLE] and time.time()< timeout:
                    time.sleep(1)
                if self.wan.status() == network.STAT_GOT_IP:
                    print("Connection successful")
                    self.server = bssid
                    return self.connect_en()
                else:
                    if time.time()>timeout:
                        print("Connection error : timeout")
                    else:
                        print(f"Connection error. status = {self.wan.status()}")

    def connect_wifi(self):
        '''Quand aucun reseau esp-non n'est accessible => WIFI
        '''
        if self.wmqtt.connect():
            self.wmqtt.callback = self.on_mqtt_message
            #refaire les subcriptions 
            for topic, callback in self.callbacks.items():
                self.wmqtt.subscribe(topic) #Eventuelement decoder en str???
            self.status['mqtt']=self.wmqtt
            self.status['timeout'] = time.time()+300
            return True

    def on_mqtt_message(self, topic, payload):
        '''on receive mqtt message
        (soit directement, soit suite on_receive message)
        '''
        print(f"Reception de {topic}=>{payload}")
        if self.callback:
            self.callback(topic, payload)
        if topic in self.callbacks:
            self.callbacks[topic](topic, payload)

    def on_receive(self, e):
        '''On receive esp-now message
        '''
        host, msg = e.irecv() 
        msg = bytes(msg)
        print(f"Reception de {msg} from {host}")
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
            print(f"oups ! message type unexpected : {type}")
            
    def send(self, data):
        if not self.e.send(self.server, data):
            print("Error sending data to server.")
        else:
            return True

    def publish(self, topic, payload, trys = 0):
        '''publish msg to mqtt broker via esp-now
        '''
        if trys >1:
            return False
        else:
            if self.status['mqtt'] == self:
                assert len(topic)+len(payload)< 248, "Message too long!"
                data = self.TYPE_PUBLISH+chr(len(topic))+topic+payload
                if not self.send(data):
                    if self.connect():
                        self.publish(topic, payload, trys+1)
            elif self.status['mqtt'] == self.wmqtt:
                self.wmqtt.publish(topic, payload)

    def subscribe(self, topic, callback = None):
        '''Subscibe to a mqtt topic via esp-now
        '''
        if self.status['mqtt'] == self:
            assert len(topic)< 248, "topic too long!"
            data = self.TYPE_SUBSCRIBE+topic
            self.send(data)

        elif self.status['mqtt'] == self.wmqtt:
            self.wmqtt.subscribe(topic)
        else:
            print("Oups, nos connection available!")
            return False
        if callback:
            self.callbacks[bytes(topic,'utf-8')]=callback
    
    def mqtt_loop(self, wait = False):
        '''Wait for mqtt message (not need if esp-now connected)
        '''
        if self.status['mqtt'] == self.wmqtt:
            self.wmqtt.loop(wait)
        else:
            pass
            #TODO : boucle avec attente callback => il faut un flag!
    def loop_forever(self):
        while True:
            self.mqtt_loop(True)


class ENClient8266(ENClient):
    '''une passerelle ESP-NOW 8266
    '''

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.init(None, None, self.on_receive)