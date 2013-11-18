#!/bin/bash

echo ========== initializing submodules
git submodule update --init --recursive

echo ========== installing prereqs
sudo apt-get install openjdk-7-jre-headless gcc build-essential yasm pkg-config libx264-dev python-dev python-setuptools lsof python-pip
easy_install --upgrade google-api-python-client
sudo pip install oauth2client
sudo pip install urllib3

echo ========== setting up python packages
cd packages/tornado
sudo python setup.py install
cd ../..

cd packages/fabric
sudo python setup.py install
cd ../..

cd packages/requests
sudo python setup.py install
cd ../..

cd packages/filemagic
sudo python setup.py install
cd ../..

cd packages/python-gnupg
sudo make install
cd ../..

echo =========== configuring and compiling ffmpeg software
cd packages/FFmpeg
./configure
make
sudo make install
cd ../..
  
sudo apt-get install ffmpeg2theora

echo =========== setting up openpgp keys
gpg --gen-key
gpg --export-secret-keys --armor (key-email-you-provided in step #1) > conf/privkey.asc
gpg --export --armor (key-email-you-provided in step #1) > conf/pubkey.asc

cd /scripts/py/
ln -s ../../conf/conf.py .

echo =======================================
echo please make sure your conf/conf.py configuration file exists and is properly configured
echo and then you may run > python scripts/py/unveillance.py start
