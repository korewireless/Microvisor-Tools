# Twilio Microvisor Bundler

This tool will take an elf compiled binary of your user code and create a bundle suitable for
distribution to a Microvisor device.

This is an initial version of this tool whose available options will expand over time.  Please
update this tool regularly during the Microvisor Beta period.

## Requirements

Assuming Ubuntu 20.04, the following are requirements for using the tool:

- apt-get install python3 python3-pip build-essential protobuf-compiler binutils-arm-none-eabi
- pip3 install cryptography
- pip3 install protobuf

A Dockerfile is also provided if you prefer to build inside of a container.

## Usage

### As a Docker Image

1. Build the container: *(IMPORTANT: you should rebuild the container after updates to the tools repository)*

```
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t mvbundler:latest .
```

2. Use the container by mapping your local directory; note that the image
   specifies `/mnt` as the WORKDIR: `docker run -v $(pwd):/mnt mvbundler:latest bundle-app --help`
3. Create a bundle from the output of the our [Demo Project](https://github.com/twilio/twilio-microvisor-freertos/):

```
docker run -v $(pwd):/mnt mvbundler:latest bundle-app gpio_toggle_demo.elf gpio_toggle_demo.zip
Bundle written to file: gpio_toggle_demo.zip
```

### App mode

You can also run the bundler directly if you are running on Ubuntu by installing the dependencies noted above and running:

```
$ python3 build_bundle.py bundle-app --help
```
