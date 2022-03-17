import time, json
import machine
import network
from esp import espnow

class ENClient():
    '''Un client de ENServer (passerelle ESP-NOW)
    '''
    TYPE_PUBLISH = b"P"
    TYPE_SUBSCRIBE = b"S"
    TYPE_MESSAGE = b"M"
    TYPE_TEST = b"T"

    def __init__(self, ssid = "ESP-NOW", timeout = 15, callback = None):
        self.ssid = ssid
        self.timeout = timeout
        self.wan = network.WLAN(network.STA_IF)#STATION
        self.wan.active(True)
        self.init_esp_now()
        self.server = None
        self.callback = callback
        self.callbacks = {} #{topic:callback, ...}
        self.load_config()
        if not self.server:
            if self.scan():
                print(f"Connected to {self.server}")
            else:
                print("Connection error!")

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.config(on_recv = self.on_receive)
        self.e.init()

    def save_config(self):
        with open("config.json", 'w') as file:
            data = {'server': self.server}
            file.write(json.dumps(data))

    def load_config(self):
        try:
            with open("config.json", 'r') as file:
                data = json.loads(file.read())
                server = data.get('server')
                if server:
                    self.server = bytes(server,"")
        except Exception as e:
            print(e)
        else:
            print(f"load config ok. server : {self.server}")
        if self.server:
            time.sleep_ms(1000)
            if not self.connect_en():
                self.server = None

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
            self.e.send(self.server, self.TYPE_TEST)
            print('.', end = '')
            time.sleep(1)
        if self.test == b"OK":
            print("Connection successful")
            return True
        else:
            print("Connection Error : timeout")


    def scan(self):
        '''Scan for WIFI AP
        '''
        print(f"Scan for {self.ssid}...")
        for ssid, bssid, channel, RSSI, authmode, hidden in self.wan.scan():
            print(f"{ssid.decode()} found. RSSI = {RSSI}")
            if ssid.decode() == self.ssid:
                print(f"Try to connect to {ssid.decode()}...")
                self.wan.connect(ssid)
                timeout = time.time() + self.timeout
                while self.wan.status() in [network.STAT_CONNECTING, network.STAT_IDLE] and time.time()< timeout:
                    time.sleep(1)
                if self.wan.status() == network.STAT_GOT_IP:
                    print("Connection successful")
                    self.server = bssid
                    if self.connect_en():
                        self.save_config()
                        return True
                else:
                    if time.time()>timeout:
                        print("Connection error : timeout")
                    else:
                        print(f"Connection error. status = {self.wan.status()}")

    def on_receive(self, e):
        host, msg = e.irecv() 
        msg = bytes(msg)
        print(f"Reception de {msg} from {host}")
        #str_host = {':'.join([str(x) for x in list(host)])}
        type = msg[0]
        if type == self.TYPE_TEST[0]:
            self.test = msg[1:]
        else:
            topic = msg[2:2+msg[1]]
            payload = msg[2+msg[1]:]
            #print(f"Reception de {topic}=>{payload} from {str_host}")
            if self.callback:
                self.callback(topic, payload)
            if topic in self.callbacks:
                self.callbacks[topic](topic, payload)
            #self.add_peer(host)

    def send(self, data):
        if not self.e.send(self.server, data):
            print("Error sending data to server.")

    def publish(self, topic, payload):
        '''publish msg to mqtt broker via esp-now
        '''
        assert len(topic)+len(payload)< 248, "Message too long!"
        data = self.TYPE_PUBLISH+chr(len(topic))+topic+payload
        self.send(data)

    def subscribe(self, topic, callback = None):
        '''Subscibe to a mqtt topic via esp-now
        '''
        assert len(topic)< 248, "topic too long!"
        data = self.TYPE_SUBSCRIBE+topic
        self.send(data)
        if callback:
            self.callbacks[bytes(topic,'utf-8')]=callback

class ENClient8266(ENClient):
    '''une passerelle ESP-NOW 8266
    '''

    def init_esp_now(self):
        self.e = espnow.ESPNow()
        self.e.init(None, None, self.on_receive)