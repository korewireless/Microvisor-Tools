# Microvisor Bundler

This tool will take a compiled binary (`.elf`) of your user code and create an application bundle suitable for distribution to a Microvisor device via the Microvisor cloud.

**IMPORTANT** Bundler is now deprecated: a more up-to-date version of its functionality is delivered by the Twilio CLI Microvisor Plugin, which should be used in preference to the code included here.

## Requirements

The standard development platform for Microvisor is [Ubuntu 20.04 LTS](https://releases.ubuntu.com/20.04/). While we hope to support other platforms in due course, for now Mac and Windows users will have to choose between interacting with the Microvisor development tools through Docker or from within a virtual machine running Ubuntu.

Bundler requires Python 3 and has a number of further dependencies. To run Bundler, first run the following commands to install its prerequisites:

- `sudo apt-get install python3 python3-pip build-essential protobuf-compiler binutils-arm-none-eabi`
- `pip3 install cryptography`
- `pip3 install protobuf~=3.0`

If you prefer to build inside a container, or are using Windows or macOS, a Dockerfile is also provided.

## Usage

### As an application

If you are running on Ubuntu, run the bundler directly, passing your `.elf` file and the name of the output `.zip` file as arguments:

```shell
python3 bundler.py path/to/your_compiled_app.elf path/to/your_bundled_app.zip
```

### As a Docker image

**IMPORTANT** You should always rebuild the container after updates to the `Microvisor-Tools` repository.

#### 1. Build the container

```shell
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t mvbundler:latest .
```

#### 2. Use the container by mapping your local directory. The image specifies `/mnt` as the `WORKDIR`:

```shell
docker run -v $(pwd):/mnt mvbundler:latest --help`
```

#### 3. Create a bundle from the output of the [FreeRTOS Demo Project](https://github.com/korewireless/Microvisor-Demo-CMSIS-Freertos):

```shell
docker run -v $(pwd):/mnt mvbundler:latest mv-freertos-cmsis-demo.elf mv-freertos-cmsis-demo.zip
```

This will output:

```shell
Bundle written to file: mv-freertos-cmsis-demo.zip
```
