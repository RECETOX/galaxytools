FROM node:24-bookworm-slim

ARG PORT=8765

ENV PORT=$PORT

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
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


# Install nvm + Node, then expose node/npm/npx in PATH for all later layers
# ENV NVM_DIR=/root/.nvm
# RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash \
#     && \. "${NVM_DIR}/nvm.sh" \
#     && nvm install "${NODE_VERSION}" \
#     && nvm alias default "${NODE_VERSION}" 

# ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin:${PATH}
# RUN node -v && npm -v 

WORKDIR /app/tad
# Clone git repo with modified code
RUN git clone -b gxit https://github.com/RECETOX/tad.git . 
    
RUN npm ci \
    && npm install \
    && npm run bootstrap \
    && ./tools/build-all.sh


WORKDIR /app/tad/packages/tadweb-server

RUN npm run build 

EXPOSE $PORT

CMD ["npm", "start"]