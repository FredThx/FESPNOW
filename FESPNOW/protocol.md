# Protocol de communication ESP-NOW <-> MQTT

## Préambule

L'idée est faire passer par ESP-NOW des messages MQTT.

### MQTT

En simplifiant, il y a deux type de messages :
* subscribe (topic)
* publish (topic, payload)

C'est le serveur (ou passerelle) qui communique en TCP/IP (WIFI ou Ethernet) avec le broker MQTT.

### ESP-NOW

Une seule chaine de 250 caractères maxi
Qui est envoyé à une addresse mac

Ce sont les clients qui l'utilisent vers le serveur
(à priori, pas entre eux)

## Protocol

### Coté  client vers server :
| mqtt | esp-now  | |
|---|---|--|
| publish(topic, payload) | "{TYPE}{LEN(topic)}{topic}{payload}"| avec TYPE = "P"|
| subscribe(topic)        | "{TYPE}{topic}"| avec TYPE = "S" |
| test connection         | '{TYPE}'  | avec TYPE = "T"|

### Coté server vers client :
msg = "{TYPE}{LEN(topic)}{topic]{payload}"  avec TYPE = "M" (mais c'est juste pour "on verra")

reponse au test : "{TYPE}OK" avec TYPE = 'T'