#!/usr/bin/env bash

if [ ! -d "po" ]; then
    echo "Error: Run this script from the project root."
    exit 1
fi

echo "Updating po/POTFILES.in..."

find data src -type f \( -name "*.desktop.in" -o -name "*.gschema.xml" -o -name "*.metainfo.xml.in" -o -name "*.py" -o -name "*.ui" \) ! -name "__init__.py" | sort > po/POTFILES.in

echo "Done."
