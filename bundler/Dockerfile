FROM ubuntu:20.04
ARG USERNAME=mvisor
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID -o $USERNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $USERNAME

RUN apt-get -yqq update \
    && apt-get install -yqq python3 python3-pip build-essential protobuf-compiler binutils-arm-none-eabi
RUN pip3 install cryptography protobuf

WORKDIR /bundler

COPY ./build_bundle.py ./bundle_pb2.py /bundler/

WORKDIR /mnt
USER $USERNAME
ENTRYPOINT ["python3", "/bundler/build_bundle.py"]
