There are a couple of customizations I make for my Pi-hole setup, documented below.

1. `99-local-no-use-AAAA.conf`: Ensures that all local requests for the domain `mattdies.com` (and subdomains as well) are kept local-only and don't use IPv6. I need this in my setup so that I can differentiate between local and remote traffic within Caddy and set some sites to "local-only". Since I don't serve my sites over IPv6 locally (only through Cloudflare), disabling IPv6 enforces all traffic to go through IPv4, where I have local DNS records for each of the sites.
1. `10-minecraft-srv.conf`: Cresates a local SRV record pointing at my PC for my Minecraft server. This enables using a domain within the Minecraft server settings, rather than an IP address.

