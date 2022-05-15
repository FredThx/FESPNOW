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


    def repl_in(self, topic, payload):
        '''Gestion du REPL : Input
        '''
        self.mqtt.publish("./REPL/OUT",exec(payload))

    



