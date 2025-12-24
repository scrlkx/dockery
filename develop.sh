#!/usr/bin/env bash

glib-compile-resources src/dockery.gresource.xml \
    --target=src/dockery.gresource \
    --sourcedir=src

flatpak-builder flatpak-build-dir com.scrlkx.dockery.json \
    --force-clean \
    --user \
    --install

flatpak run com.scrlkx.dockery//master
