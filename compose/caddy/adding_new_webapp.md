# Adding a New Web-app in Caddy
## Table of Contents
- [But first... "hairpinning"](#but-first-hairpinning)
- [Pi-hole](#pi-hole)
	- [AAAA (IPv6) Records](#aaaa-ipv6-records)
- [Public DNS Records](#public-dns-records)
	- [Manual (Not Recommended)](#manual-not-recommended)
	- [Automatic, Using Caddy Plug-ins](#automatic-using-caddy-plug-ins)

## But first... "hairpinning"
We want [NAT loopback/"hairpinning"](https://nordvpn.com/cybersecurity/glossary/nat-loopback/) so that I can distinguish between local and remote traffic and make some (most) web-apps "local only".
As a security measure, I'm choosing to only serve apps to the world that are completely necessary, like Overseerr.
When Caddy can distinguish between local and remote traffic, we're able to restrict chosen access to chosen web-apps to local-only using the below snippet:
```
(local_network_only) {
	@external not remote_ip <your local subnet here>
	respond @external 403
}
```
Then using it like so:
```
domain_name.com {  # replace with your domain name
	import local_network_only
	reverse_proxy <local IP + port>
}
```

## Pi-hole
In order to enable NAT loopback, we need to have a local DNS that can route traffic to local IP addresses.
Luckily, I've already got a local DNS... two of them actually!
It's easy to forget that Pi-hole is a DNS because it gets a reputation as an "ad-blocker".
Which it is, but it does it as a DNS sinkhole, a.k.a. a server!

**This means we need to register local DNS A records on both of the Pi-hole servers for each new web-app.**
Navigate to `/admin/dns_records.php` in order to add new domain registrations.
Add the relevant domain and IP address to the relevant boxes and click "Add".
In this case, the domain is the desired domain for the application that you're configuring in Caddy and the IP address should be the local IP address of the device running the application.

### AAAA (IPv6) Records
Many public DNS services will route for both IPv4 and IPv6.
If you're like me and don't have IPv6 within the network, you'll have to prevent Pi-hole from using the available AAAA records for the domain name.
Otherwise, Pi-hole will allow the request but may use the AAAA record from Cloudflare, rather than the local A record we just set up.
This means that despite our local DNS records, the traffic may still leave your network and you will be met with a 403 when accessing your webpages.

To solve this, you can add a custom `99-local-no-use-AAAA.conf` file to the `/etc/dnsmasq.d` directory within the container, like so.
```env
# Keep domain_name.com and all subdomains local, and disable IPv6
local=/domain_name.com/
```
Of course, you should change this to your domain as needed.
This will cover all subdomains of the domain as well, e.g., `auth.domain_name.com`.
If you're running Pi-hole in Docker, you'll have to make sure that this file is stored within a volume mount so that the changes persist when the container is stopped.

## Public DNS Records
### Manual (Not Recommended)
You'll also have to register the appropriate DNS record for your domain through your DNS service.
For me, this is Cloudflare.
Navigate to the appropriate domain and edit the associated DNS records.
You'll have to add `A` records for your desired subdomain as well as `www.<subdomain>`.
Point the IP address to the public IP address of your server.

### Automatic, Using Caddy Plug-ins
If you'd like to avoid the manual process of adding the records (especially if your public IP address will be changing), then you can add some plug-ings to do this.
These examples are for Cloudflare, but there are plenty of plug-ins out there for other popular DNS services.

* https://github.com/caddy-dns/cloudflare: "This package contains a DNS provider module for Caddy. It can be used to manage DNS records with Cloudflare accounts."
	> I created a snippet that I use in every website to use Cloudflare for TLS:
	```
	(cloudflare_dns) {
		tls {
			dns cloudflare {env.CLOUDFLARE_API_TOKEN}
		}
	}
	```
	If you do this as well, be sure to set the `SSL/TLS encryption` option within Cloudflare to `Full (strict)`.
* https://github.com/WeidiDeng/caddy-cloudflare-ip: "This module retrieves cloudflare ips from their offical website, ipv4 and ipv6. It is supported from caddy v2.6.3 onwards."
	> I set this in my global settings to add Cloudflare to my trusted proxies automatically:
	```
	trusted_proxies cloudflare {
		interval 12h
		timeout 15s
	}
	```
* https://github.com/mholt/caddy-dynamicdns: "This is a simple Caddy app that keeps your DNS pointed to your machine; especially useful if your IP address is not static."
	> Finally, let's have our DNS records be automatically generated in Cloudflare.
	The below as a global setting will use Cloudflare to register domains for the `domain_name.com` domain, as well as the subdomain `www` (meaning `www.domain_name.com`).
	The `dynamic_domains` option will look through your Caddyfile and find all domains matching the given domain and register records for those.
	So for example, if you have `auth.domain_name.com` below, the plug-in will handle this subdomain as well.
	```
	dynamic_dns {
		provider cloudflare {env.CLOUDFLARE_API_TOKEN}
		domains {
			domain_name.com www
		}
		versions ipv4
		dynamic_domains
	}
	```

You may notice that I'm using the `{env.CLOUDFLARE_API_TOKEN}` variable in the examples.
In order to create this token, you can check out the documentation for the awesome tools above.
The environment variable is set inside the container via an entrypoint script I've created to read the contents of Docker secret files, set them as environment variables, and then execute a given entrypoint passed to it.
For more information, check out [`scripts/set_secret_vars.sh`](../../scripts/set_secret_vars.sh) to see the script and `compose/caddy/caddy-compose.yaml`'s [`entrypoint`](caddy-compose.yaml#L13) key and [mounted volume](caddy-compose.yaml#L26) to see it in use.
