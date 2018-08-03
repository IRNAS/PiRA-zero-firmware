FROM resin/rpi-python:latest

# Switch on systemd init system in container.
ENV INITSYSTEM on

# Set the working directory.
WORKDIR /usr/src/app

# Install system package dependencies.
RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -yq --no-install-recommends \
        i2c-tools python-smbus pigpio libfreetype6-dev libjpeg-dev build-essential \
        wget \
	unzip \
	libtool \
	pkg-config \
	autoconf \
	automake \
	net-tools \
	can-utils \
	make \ 
	dnsmasq && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install resin-wifi-connect.
#RUN curl https://api.github.com/repos/resin-io/resin-wifi-connect/releases/latest -s \
 #   | grep -hoP 'browser_download_url": "\K.*%%RESIN_ARCH%%\.tar\.gz' \
  #  | xargs -n1 curl -Ls \
   # | tar -xvz -C /usr/src/app/

# This environmental variable is required to build latest picamera.
ENV READTHEDOCS True

# Install python package dependencies.
COPY ./requirements.txt /requirements.txt

RUN pip install --extra-index-url=https://www.piwheels.org/simple -r /requirements.txt -v

# Copy everything into the container.
COPY . ./

# Setup entry point.
CMD ["bash", "start.sh"]
