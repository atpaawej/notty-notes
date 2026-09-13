project('notty', version: '0.1.5', meson_version: '>= 0.59')

python = import('python').find_installation('python3')
install_subdir('src/notty', install_dir: python.get_install_dir())

install_data('data/app.notty.Notty.desktop', install_dir: get_option('datadir') / 'applications')
install_data('data/app.notty.Notty.metainfo.xml', install_dir: get_option('datadir') / 'metainfo')
install_data('data/app.notty.Notty.gschema.xml', install_dir: get_option('datadir') / 'glib-2.0' / 'schemas')
install_data('data/style.css', install_dir: get_option('datadir') / 'notty')
install_data('data/notty.png', install_dir: get_option('datadir') / 'icons' / 'hicolor' / '512x512' / 'apps', rename: 'app.notty.Notty.png')
install_data('data/notty.png', install_dir: get_option('datadir') / 'icons' / 'hicolor' / '256x256' / 'apps', rename: 'app.notty.Notty.png')
install_data('data/notty.png', install_dir: get_option('datadir') / 'icons' / 'hicolor' / '128x128' / 'apps', rename: 'app.notty.Notty.png')

# dev run: python -m notty --dev
