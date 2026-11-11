# Let's build a custom image to add a rate-limiting module
# For more information, see "Adding custom Caddy modules" on the below:
# https://hub.docker.com/_/caddy

FROM caddy:2-builder-alpine@sha256:a0fde94c08a09fc31a8f2aeb42d0c2003807a325f04efeb98fa6cc89e25682e0 AS builder

RUN <<EOF
xcaddy build \
    --with github.com/mholt/caddy-ratelimit \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/WeidiDeng/caddy-cloudflare-ip \
    --with github.com/mholt/caddy-dynamicdns
EOF

# -----------------

FROM caddy:2-alpine@sha256:78bd35025c7ba85961dd149ae670315129954e77abe2383ac47c89106b35ade9

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
