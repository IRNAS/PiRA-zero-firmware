#!/bin/bash

url -X POST --header "Content-Type:application/json" \
    "$RESIN_SUPERVISOR_ADDRESS/v1/shutdown?apikey=$RESIN_SUPERVISOR_API_KEY"
