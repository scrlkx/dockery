# Show available recipes.
default:
  @just --list

# Build/install Flatpak bundle and run app with LANG (default: en).
develop lang="en":
  meson compile -C _build dockery-pot

  flatpak-builder flatpak-build-dir com.scrlkx.dockery.json \
    --force-clean \
    --user \
    --install

  flatpak run --env=LANG="{{lang}}.UTF-8" com.scrlkx.dockery//master

# Regenerate Flatpak Python dependency manifest.
update-flatpak-deps:
  req2flatpak \
    --requirements-file requirements.txt \
    --target-platforms 312-x86_64 312-aarch64 \
    --yaml > com.scrlkx.dockery.py-deps.yml

# Refresh po/POTFILES.in from translatable sources.
update-potfiles:
  find data src -type f \
    \( -name "*.desktop.in" -o -name "*.gschema.xml" -o -name "*.metainfo.xml.in" -o -name "*.py" -o -name "*.ui" \) \
    ! -name "__init__.py" \
    | sort > po/POTFILES.in

# Update all translation files listed in po/LINGUAS.
update-translations:
  if [ ! -d "_build" ]; then meson setup _build; fi
  meson compile -C _build dockery-pot
  while read -r lang; do \
    if [ -f "po/$lang.po" ]; then \
      msgmerge --update --no-fuzzy-matching --backup=off "po/$lang.po" po/dockery.pot; \
    else \
      msginit --no-translator --locale="$lang" --input=po/dockery.pot --output="po/$lang.po"; \
    fi; \
  done < po/LINGUAS
