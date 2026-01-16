#!/usr/bin/env bash

meson compile -C _build dockery-pot

flatpak-builder flatpak-build-dir com.scrlkx.dockery.json \
    --force-clean \
    --user \
    --install

read -p "Language (e.g. pt_BR, optional): " lang

if [ -n "$lang" ]; then
    flatpak run --env=LANG=$lang.UTF-8 com.scrlkx.dockery//master
else
    flatpak run com.scrlkx.dockery//master
fi
