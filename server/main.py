import time
import network
from FESPNOW.en_server import ENServer
from FESPNOW.mqtt_pass import MqttPasse

esp_now = ENServer()
mqtt = MqttPasse('WIFI_THOME2', 'plus33324333562', '192.168.10.155', autoconnect = True)
esp_now.link(mqtt)

mqtt.loop_forever()