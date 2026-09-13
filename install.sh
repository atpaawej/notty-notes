#!/usr/bin/env bash
# Notty installer - curl | bash friendly
# Usage: curl -fsSL https://raw.githubusercontent.com/atpaawej/notty-notes/master/install.sh | bash
#     or: wget -qO- https://raw.githubusercontent.com/atpaawej/notty-notes/master/install.sh | bash
set -e

REPO="atpaawej/notty-notes"
VERSION="0.1.5"
DEB="notty_${VERSION}_all.deb"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/master"
RELEASE_URL="https://github.com/${REPO}/releases/download/v${VERSION}/${DEB}"
RAW_DEB_URL="${RAW_BASE}/dist/${DEB}"

echo "→ Notty installer v${VERSION}"

# detect distro
if ! command -v apt >/dev/null 2>&1; then
  echo "✗ apt not found. Manual install: sudo dpkg -i ${DEB}"
  exit 1
fi

# deps
echo "→ Installing dependencies (needs sudo)..."
sudo apt update -qq
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtksource-5 curl wget

TMPDIR="$(mktemp -d)"; trap 'rm -rf "$TMPDIR"' EXIT

# try release asset first, fallback to raw dist/
DEB_PATH="${TMPDIR}/${DEB}"
echo "→ Downloading ${DEB}..."
if curl -fsSL -o "${DEB_PATH}" "${RELEASE_URL}" 2>/dev/null; then
  echo "  from release: ${RELEASE_URL}"
elif curl -fsSL -o "${DEB_PATH}" "${RAW_DEB_URL}" 2>/dev/null; then
  echo "  from raw: ${RAW_DEB_URL}"
else
  echo "→ No .deb found, installing from source..."
  if [ -d "./src/notty" ]; then
    echo "  local source found"
    SRC="."
  else
    echo "  cloning ${REPO}..."
    git clone --depth 1 "https://github.com/${REPO}.git" "${TMPDIR}/src" 2>/dev/null || {
      echo "✗ git not found, install git or download .deb manually:"
      echo "  wget ${RAW_DEB_URL} && sudo dpkg -i ${DEB}"
      exit 1
    }
    SRC="${TMPDIR}/src"
  fi
  echo "→ Installing from source to /usr/lib/python3/dist-packages..."
  sudo mkdir -p /usr/lib/python3/dist-packages /usr/bin /usr/share/applications /usr/share/glib-2.0/schemas /usr/share/metainfo
  sudo cp -r "${SRC}/src/notty" /usr/lib/python3/dist-packages/
  sudo cp "${SRC}/data/app.notty.Notty.desktop" /usr/share/applications/
  sudo cp "${SRC}/data/app.notty.Notty.gschema.xml" /usr/share/glib-2.0/schemas/
  sudo cp "${SRC}/data/app.notty.Notty.metainfo.xml" /usr/share/metainfo/
  sudo tee /usr/bin/notty >/dev/null <<'EOS'
#!/usr/bin/env python3
import sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")
from notty.app import run
if __name__ == "__main__":
    run()
EOS
  sudo chmod +x /usr/bin/notty
  sudo glib-compile-schemas /usr/share/glib-2.0/schemas 2>/dev/null || true
  sudo update-desktop-database -q 2>/dev/null || true
  echo "✓ Notty installed from source. Run: notty"
  exit 0
fi

echo "→ Installing .deb..."
sudo dpkg -i "${DEB_PATH}" || sudo apt-get install -f -y
rm -rf "${TMPDIR}"

if command -v notty >/dev/null 2>&1; then
  echo "✓ Notty installed. Run: notty"
  notty --headless 2>&1 | head -n 1 || true
else
  echo "✗ Install failed, try: sudo dpkg -i ${DEB}"
  exit 1
fi
