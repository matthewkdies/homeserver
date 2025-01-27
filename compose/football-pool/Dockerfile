ARG PYTHON_TAG=3.12-alpine

FROM python:${PYTHON_TAG}

EXPOSE 5600

ARG USER=notroot
ARG UID=${UID}
ARG GID=${GID}

ENV APPS_DIR=/apps \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=football_pool \
    FLASK_DEBUG=0 \
    FLASK_ENV=production \
    TZ=UTC

RUN <<EOF
sed -i 's/https/http/' /etc/apk/repositories && \
addgroup --system --gid ${GID} ${USER} && \
adduser --system --uid ${UID} -G ${USER} ${USER}
mkdir --parents ${APPS_DIR}/football_pool/
EOF

COPY --chown=${USER}:${USER} requirements.txt package.json package-lock.json ${APPS_DIR}/football_pool/

RUN <<EOF
apk add --no-cache curl gcc g++ musl-dev postgresql-dev libpq-dev make nodejs npm && \
npm --prefix ${APPS_DIR}/football_pool install && \
pip --no-cache-dir install -r ${APPS_DIR}/football_pool/requirements.txt && \
mkdir ${APPS_DIR}/migrations && \
chown 1000:1000 ${APPS_DIR}/migrations
EOF

COPY --chown=${USER}:${USER} ./tailwind.config.js ${APPS_DIR}
COPY --chown=${USER}:${USER} ./apps/football_pool ${APPS_DIR}/football_pool

# we make sure to run the project as a regular user
USER ${USER}

WORKDIR ${APPS_DIR}

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5600", "football_pool:create_app()"]
