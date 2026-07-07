FROM node:24-bookworm-slim

ARG PORT=8765

ENV PORT=$PORT

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    xz-utils \
    &&  apt-get clean \
    &&  apt-get autoclean \
    &&  apt-get autoremove --yes \
    &&  rm -rf /var/lib/apt/lists/* \
    &&  rm -rf /var/lib/dpkg/ \
    &&  rm -rf /var/cache/ \
    &&  rm -rf /var/log/ \
    &&  rm -rf /tmp/* ;

WORKDIR /app/tad
# Clone git repo with modified code
RUN git clone -b gxit https://github.com/RECETOX/tad.git . 
    
RUN npm ci \
    && npm install \
    && npm run bootstrap \
    && ./tools/build-all.sh

WORKDIR /app/tad/packages/tadweb-server

RUN npm run build && npm cache clean --force

EXPOSE $PORT

CMD ["npm", "start"]
