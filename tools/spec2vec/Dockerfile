FROM python:3.9

ARG COMMIT_SHA=c9b54b950e0dbb8053ba95aabdb2d815e11e7503

WORKDIR /spec2vec

# download src
RUN wget -O /tmp/$COMMIT_SHA.zip https://github.com/iomega/spec2vec/archive/${COMMIT_SHA}.zip && \
    unzip /tmp/${COMMIT_SHA}.zip

# install spec2vec
RUN pip install ./spec2vec-${COMMIT_SHA}
