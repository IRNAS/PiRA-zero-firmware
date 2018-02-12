#!/bin/bash

for i in 1 2 3 4 5; do curl -X POST --header "Content-Type:application/json" "$RESIN_SUPERVISOR_ADDRESS/v1/reboot?apikey=$RESIN_SUPERVISOR_API_KEY" && break || sleep 15; done
