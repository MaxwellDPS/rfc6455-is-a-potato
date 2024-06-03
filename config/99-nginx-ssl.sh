#!/bin/bash

mkdir -p /etc/nginx/ssl/
CERT_FILE="/etc/nginx/ssl/server.crt"
KEY_FILE="/etc/nginx/ssl/server.key"

# Check if the certificate file exists
if [ ! -f "$CERT_FILE" ]; then
  echo "Certificate file not found. Generating a new self-signed EC certificate..."

# # Generate the EC key
#   openssl ecparam -genkey -name prime256v1 -out "$KEY_FILE"

#   # Generate the self-signed certificate using the EC key
#   openssl req -x509 -nodes -days 365 -key "$KEY_FILE" -out "$CERT_FILE" -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=www.example.com"

  openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=www.example.com"


  echo "Self-signed EC certificate with a secure key generated successfully."
else
  echo "Certificate file already exists. Skipping generation."
fi

