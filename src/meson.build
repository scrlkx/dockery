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

dockery_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'container_page.py',
  'containers_page.py',
]

install_data(dockery_sources, install_dir: moduledir)
