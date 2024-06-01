#!/bin/bash

if [ "$EUID" -ne 0 ]
then
    echo "Please run with sudo"
    echo "sudo -Es ./$0 $@"
    exit
fi

OS_CODENAME=`lsb_release -cs`

install_cloudflared () {
    # Add cloudflare gpg key
    sudo mkdir -p --mode=0755 /usr/share/keyrings
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

    # Add this repo to your apt repositories
    echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $OS_CODENAME main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

    # install cloudflared
    sudo apt-get update && sudo apt-get install cloudflared
}




install_cloudflared


