#!/bin/bash

echo ========== initializing submodules
git submodule update --init --recursive

echo ========== installing prereqs
sudo apt-get install openjdk-7-jre-headless gcc build-essential yasm pkg-config libx264-dev python-dev python-setuptools lsof python-pip
easy_install --upgrade google-api-python-client
sudo pip install oauth2client
sudo pip install urllib3

echo ========== setting up python packages
cd packages/tornado/
sudo python setup.py install
cd ../..
pwd

cd packages/fabric/
sudo python setup.py install
cd ../..
pwd

cd packages/requests/
sudo python setup.py install
cd ../..

pwd
cd packages/filemagic/
sudo python setup.py install
cd ../..

pwd
cd packages/python-gnugp
sudo make install
cd ../..

pwd
cd packages/JavaMediaHasher/
ant dist
cd ../..

echo =========== configuring and compiling ffmpeg software
cd packages/FFmpeg
./configure
make
sudo make install
cd ../..
  
sudo apt-get install ffmpeg2theora

cd scripts/py/
ln -s ../../conf/conf.py .
cd ../..

echo =======================================
echo now setup GPG key and export it properly as indicated in the README file
echo please make sure your conf/conf.py configuration file exists and is properly configured
echo and then you may run scripts/py/unveillance.py start
