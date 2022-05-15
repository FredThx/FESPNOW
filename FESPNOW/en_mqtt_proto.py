# coding: utf-8


class ENMqttProto:
    '''A communication protocol ESP-NOW <-> MQTT
    '''
    TYPE_PUBLISH = b"P"
    TYPE_SUBSCRIBE = b"S"
    TYPE_MESSAGE = b"M"
    TYPE_TEST = b"T"
    TYPE_SSID = b'W'
    TYPE_PASSW = b'A'
    TYPE_HOST = b'H'
