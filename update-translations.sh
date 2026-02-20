#!/usr/bin/env bash

set -e

if [ ! -d "_build" ]; then
    meson setup _build
fi

meson compile -C _build dockery-pot

for lang in $(cat po/LINGUAS); do
    if [ -f "po/${lang}.po" ]; then
        msgmerge --update --no-fuzzy-matching --backup=off "po/${lang}.po" po/dockery.pot
        echo "Updated: po/${lang}.po"
    else
        msginit --no-translator --locale="${lang}" --input=po/dockery.pot --output="po/${lang}.po"
        echo "Created: po/${lang}.po"
    fi
done
