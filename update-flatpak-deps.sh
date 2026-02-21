#!/bin/bash

req2flatpak \
    --requirements-file requirements.txt \
    --target-platforms 312-x86_64 312-aarch64 \
    --yaml > com.scrlkx.dockery.py-deps.yml
