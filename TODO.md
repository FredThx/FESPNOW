# Serveur EN:

- [ ] gérer le keep alive des clients (s'inspirer de mqtt avec ses PINGREQ et PINGRESP). Mais attention le unsubscribe n'est pas implémenté dans notre micropython. masi il faut prévoir un keepalive très long!
- [ ] broadcast. Mais pour quoi faire?

- [ ] décentraliser le bazard : les clients peuvent être serveurs. (attention c'est plien de pièges ce truc là).
- [ ] couper le wifi en mode AP quand pas nécessaire. mais comment savoir qu'il n'y a pas un client qui cherche une adresse mac? N'y aurait-il pas une sorte de ARP sur esp-now
- [ ] Utiliser vraiment l'intêret de la chose : peu d'energie consommé, souvent en veille.
- [ ] Utiliser le Wifi/mqtt sur les clients quand esp-now ne passe pas.
- [ ] envisager en connexion entre esp server et raspberry pi via sérial coté esp-now et ethernet coté mqtt. Mais est-ce vraiment utile?
- [ ] trouver une solution pour dépasser la limite du nombre de peers connectés. peux-être suffit-il de ne pas faire les add_peer?
