# Par rapport à Pymarkr et les repertoires

La librairie commune à tous les projets : FESPNOW

Mais comme avec Pymarkr, 
* on ne peut pas uploader vers les microcontroleur plusieurs dossiers
* je ne veux pas dupliquer les mêmes fichiers à plusieurs endroits

la solution : faire des liens symbolics entre ./FESPNOW et ./my_device/FESPNOW

mais pour le pas simplier, c'est hébergé sur le NAS et l'on ne peut pas faire de lien symbolic, mais juste des mounts

à faire à chaque device :

en ssh sur le nas : 

mkdir /volume1/Devlopp/FESPNOW/devices/mydevice/FESPNOW
sudo mount --bind /volume1/Devlopp/FESPNOW/FESPNOW /volume1/Devlopp/FESPNOW/devices/mydevice/FESPNOW

et pour le rendre permanent : dans /etc/rc.local