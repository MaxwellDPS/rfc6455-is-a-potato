docker run cloudflare/cloudflared:latest tunnel --no-autoupdate --hello-world

docker run --rm -it -v ./.cloudflared:/home/nonroot/.cloudflared cloudflare/cloudflared:latest tunnel login