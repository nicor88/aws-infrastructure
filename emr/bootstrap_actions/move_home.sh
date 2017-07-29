#!/usr/bin/env bash

# home backup
if [ ! -d /mnt/home_backup ]; then
  sudo mkdir /mnt/home_backup
  sudo cp -a /home/* /mnt/home_backup
fi

# mount home to /mnt
if [ ! -d /mnt/home ]; then
  sudo mv /home/ /mnt/
  sudo ln -s /mnt/home /home
fi
