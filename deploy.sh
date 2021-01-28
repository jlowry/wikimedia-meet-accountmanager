#!/bin/sh
set -e

dpkg-buildpackage -rfakeroot -us -uc -b
sudo apt remove python3-meet-accountmanager
sudo apt clean
sudo apt install ../python3-meet-accountmanager_0.1.0-1_all.deb
sudo systemctl restart meet-accountmanager.service

