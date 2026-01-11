#!/usr/bin/env bash

meson compile -C _build dockery-pot

flatpak-builder flatpak-build-dir com.scrlkx.dockery.json \
    --force-clean \
    --user \
    --install

flatpak run com.scrlkx.dockery//master
