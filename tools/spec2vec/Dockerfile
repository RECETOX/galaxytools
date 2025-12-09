FROM python:3.9

ARG COMMIT_SHA=9eaefa3ecee9649e8822549eaa6275f11d84ad44

WORKDIR /spec2vec

# download src
RUN wget -O /tmp/$COMMIT_SHA.zip https://github.com/iomega/spec2vec/archive/${COMMIT_SHA}.zip && \
    unzip /tmp/${COMMIT_SHA}.zip

# install spec2vec
RUN pip install ./spec2vec-${COMMIT_SHA}
