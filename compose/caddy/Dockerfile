# Let's build a custom image to add a rate-limiting module
# For more information, see "Adding custom Caddy modules" on the below:
# https://hub.docker.com/_/caddy

FROM caddy:2-builder-alpine@sha256:ef9b65adf9a224770c6d5f6d1ae1bf99bc3caaa78d8c4bae3ea949ee6984f301 AS builder

RUN <<EOF
xcaddy build \
    --with github.com/mholt/caddy-ratelimit \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/WeidiDeng/caddy-cloudflare-ip \
    --with github.com/mholt/caddy-dynamicdns
EOF

# -----------------

FROM caddy:2-alpine@sha256:24ec7b05bc532c7bb57f727030c5056e257ff7138b4b50460306819ff79362bd

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
