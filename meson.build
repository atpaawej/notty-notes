project('notty', version: '0.1.1', meson_version: '>= 0.59')

python = import('python').find_installation('python3')
install_subdir('src/notty', install_dir: python.get_install_dir())

install_data('data/app.notty.Notty.desktop', install_dir: get_option('datadir') / 'applications')
install_data('data/app.notty.Notty.metainfo.xml', install_dir: get_option('datadir') / 'metainfo')
install_data('data/app.notty.Notty.gschema.xml', install_dir: get_option('datadir') / 'glib-2.0' / 'schemas')

# dev run: python -m notty --dev
