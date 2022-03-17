'''
Projet  : FESPNOW
Auteur : FredThx
'''

import network, json
from esp import espnow

class ENServer():
    '''Une passelle ESP-NOW (a priori ESP32)
    '''
    TYPE_PUBLISH = b'P' #todo : mettre ca dans une entete et harmoniser typage
    TYPE_SUBSCRIBE = b'S'
    TYPE_MESSAGE = b"M"
    TYPE_TEST = b"T"

    def __init__(self, ssid = "ESP-NOW", channel = 11, callback = None):
        '''
            ssid            :   SSID for AP on this device (needed to share mac addr)
            channel         :   channel for AP on this device
            callback        :   callback function on message received args : host, msg
        '''
        self.ssid = ssid
        self.mqtt_publish = callback
        self.mqtt_subscribe = None
        self.subscriptions = {}
        self.wan = network.WLAN(network.AP_IF) #POINT D'ACCES
        self.wan.config(essid=ssid, channel = channel)
        self.wan.active(True)
        self.init_esp_now()
        self.load_config()
        

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.config(on_recv = self.on_receive)
        self.e.init()

    def on_receive(self, e):
        '''on receive incoming ESP-NOW message
        '''
        host, msg = e.irecv() 
        msg = bytes(msg)
        str_host = {':'.join([str(x) for x in list(host)])}
        print(f"Reception de {type(msg)}({msg}) from {str_host}")
        self.add_peer(host)
        print(f"msg[0]='{msg[0]}', msg[0]=='P' = {msg[0]=='P'}")
        if msg[0] == self.TYPE_TEST[0]:
            print(f"message TEST received from {host}")
            payload = self.TYPE_TEST+"OK"
            self.e.send(host,payload)
        elif self.mqtt_publish and msg[0] == self.TYPE_PUBLISH[0]:
            topic = msg[2:2+msg[1]]
            payload = msg[2+msg[1]:]
            self.mqtt_publish(topic, payload)
            #print(f"message routed to mqtt : '{topic}'=>'{payload}'")
        elif self.mqtt_subscribe and  msg[0] == self.TYPE_SUBSCRIBE[0]:
            topic = msg[1:]
            self.subscribe(host, topic)
            #print(f"Subsciption done for '{topic}'=>'{str_host}'")
        else:
            print("oups, nothing to do with this message!")
    
    def subscribe(self, host, topic):
        '''Subscribe a topic on mqtt broker for host
        '''
        print(f"subscribe({host},{type(topic)}({topic})")
        self.subscriptions[topic] = bytes(host)
        if self.mqtt_subscribe:
            self.mqtt_subscribe(topic)
        self.save_config()

    def on_mqtt_incoming(self, topic, payload):
        '''When a mqtt message come
        '''
        #print(f"on_mqtt_incoming(self, {type(topic)} {topic}, {type(payload)} {payload}):")
        payload = self.TYPE_MESSAGE+chr(len(topic))+topic+payload
        if topic == b"#":#TODO
            self.e.send(payload)
        else:
            if topic in self.subscriptions:
                host = self.subscriptions[topic]
                self.e.send(host, payload)
            else:
                print(f'no peer for this topic : {topic}')

    def add_peer(self, peer):
        '''pas vraiment utilisé actuellement.
        A voir si besoin de broadcast
        '''
        try:
            self.e.add_peer(peer)
        except OSError as e:
            pass#print(e)
        else:
            print(f"new peer added : {peer}")
            self.save_config()  

    def link(self, mqtt):
        '''Connect les deux reseaux ESP-NOW <-> WIFI-MQTT
        '''
        #ESP-NOW => WIFI-MQTT
        self.mqtt_publish = mqtt.publish
        self.mqtt_subscribe = mqtt.subscribe
        #WIFI-MQTT- => ESP-MQTT
        mqtt.callback = self.on_mqtt_incoming
        #Subscribe for all topic saved
        for topic in self.subscriptions:
            self.mqtt_subscribe(topic)

    
    def get_peers(self):
        return [p[0] for p in self.e.get_peers()]

    def save_config(self):
        '''Save the config in a sjon file
        '''
        if not self._load_config:
            print("Save config")
            data = {}
            data['peers'] = self.get_peers()
            data['subscriptions'] = self.subscriptions
            with open("config.json","w") as file:
                file.write(json.dumps(data))

    def load_config(self):
        '''Read the configuration file
        and load peers and subscritions
        '''
        self._load_config = True
        data = None
        try:
            with open("config.json", 'r') as file:
                data = json.loads(file.read())
        except Exception as e:
            print(e)
        else:
            if "peers" in data:
                for peer in data['peers']:
                    self.add_peer(peer)
            if "subscriptions" in data:
                for topic, host in data['subscriptions'].items():
                    self.subscribe(bytes(host,None), bytes(topic, None))
            print("load config ok")
        self._load_config = False
            
class ENServer8266(ENServer):
    '''une passerelle ESP-NOW 8266
    '''

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.init(None, None, self.on_receive)