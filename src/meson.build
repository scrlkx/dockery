pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'dockery'
gnome = import('gnome')

gnome.compile_resources('dockery',
  'dockery.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'dockery.in',
  output: 'dockery',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

install_data([
  '__init__.py',
  'main.py',
  'window.py',
], install_dir: moduledir)

install_data([
  'components/__init__.py',
  'components/badge.py',
  'components/key_value_row.py',
], install_dir: moduledir / 'components')

install_data([
  'pages/__init__.py',
  'pages/container_page.py',
  'pages/containers_page.py',
], install_dir: moduledir / 'pages')

install_data([
  'utils/__init__.py',
  'utils/events.py',
  'utils/docker.py',
  'utils/ui.py',
], install_dir: moduledir / 'utils')
