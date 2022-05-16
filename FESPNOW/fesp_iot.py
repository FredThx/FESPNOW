import os
from FESPNOW.en_client import *
from FESPNOW.wd import WDT
from machine import Timer

class FESPIot:
    """Un object connecté
    """
    def __init__(self, mqtt_base_topic, watchdog = None, wifi = None):
        '''
        mqtt_base_topic  :
        watchdog         :   en seconds
        wifi             :   a dict {'ssid' : ..., 'passw' : ..., 'host'} if not None, force wifi connection
        '''
        self.mqtt_base_topic = mqtt_base_topic
        if self.mqtt_base_topic[-1] == '/':
            self.mqtt_base_topic = self.mqtt_base_topic[:-1]
        if os.uname().sysname == 'esp8266':
            self.mqtt =ENClient8266(mqtt_base_topic = mqtt_base_topic, wifi = wifi)
        else:
            self.mqtt =ENClient(mqtt_base_topic = mqtt_base_topic, wifi = wifi)
        if watchdog:
            assert type(watchdog)==int,"Watchdog must be a integer"
            self.wdt = WDT(watchdog)
            self.mqtt.subscribe("./WDT", lambda topic, payload : self.wdt.feed())
            self.tim_wdt = Timer(-1)
            self.tim_wdt.init(mode = Timer.PERIODIC, period = watchdog*500, callback = lambda tim:self.mqtt.publish("./WDT","OK"))
            self.wdt.enable()
        #REPL via MQTT
        self.mqtt.subscribe("./REPL/IN", self.repl_in)
        # Les messages
        self.mqtt_out_topics = {}
        self.mqtt_in_topics = {}
        self.tim_read_and_send = Timer(-1)


    def repl_in(self, topic, payload):
        '''Gestion du REPL : Input
        '''
        self.mqtt.publish("./REPL/OUT",exec(payload))
        
    def run_forever(self, interval=600):
        '''Add a timer to read_and_send
        interval    :   seconds (default : 10 minutes)
        '''
        def tim_callback(t):
            self.read_and_send()
        self.tim_read_and_send.init(mode = Timer.PERIODI, period = interval * 1000, callback = tim_callback)

    def stop(self):
        '''Stop the timer
        '''
        self.tim_read_and_send.deinit()


    def read_and_send(self):
        '''Read and send all mqtt_out_topic
        '''
        for topic in self.mqtt_out_topics:
            self.send_out_topic(topic)

    def add_out_topic(self, topic, **kwargs):#message, qos = 0, retain = 0, callback = None, manual = False):
        '''Add new output topic
        message : a value, a function,  ... todo
        callback : function callback when mqtt broker get message
        '''
        self.mqtt_out_topics['topic'] = kwargs
        #
        self.add_in_topic(topic, "SENDIT", lambda : self.send_out_topic(topic))

    def send_out_topic(self, topic):
        '''
        Send output topic'''
        if message:=self.mqtt_out_topics.get(topic):
            if callable(message):
                message = message()#des arguments???
            self.mqtt.publish(topic, str(message))#TODO : qos, callbac, ...

    def add_in_topic(self, topic, payload = None, callback = None):
        '''Add a new input
        callback : function(topic, payload)
        '''
        def function_callback(_topic, _payload):
            if payload is None or payload == _payload:
                if callable(callback):
                    message = callback(_topic, _payload)
                else:
                    message = callback
                if message:
                    self.mqtt.publish(_topic, message)
        self.mqtt.subscribe(topic, function_callback)

        



