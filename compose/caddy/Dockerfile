# Let's build a custom image to add a rate-limiting module
# For more information, see "Adding custom Caddy modules" on the below:
# https://hub.docker.com/_/caddy

ARG CADDY_VERSION

FROM caddy:${CADDY_VERSION:-2.10.2}-builder-alpine AS builder

RUN <<EOF
xcaddy build \
    --with github.com/mholt/caddy-ratelimit \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/WeidiDeng/caddy-cloudflare-ip \
    --with github.com/mholt/caddy-dynamicdns
EOF

# -----------------

ARG CADDY_VERSION

FROM caddy:${CADDY_VERSION:-2.10.2}-alpine

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
