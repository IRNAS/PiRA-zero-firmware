#/bin/bash

I2C_BUS=1 # Default i2c bus number
modprobe i2c-dev


#Starts our sensor read script.
nohup python src/sensor.py &
echo "Started sensors"
nohup python gpio_example.py &
echo "Started gpio"
