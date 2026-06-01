#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
SPA_DIR="$BACKEND_DIR/static/spa"
ENV_FILE="$BACKEND_DIR/.env"
FRONTEND_ENV_FILE="$FRONTEND_DIR/.env"
OS_ID=""
OS_LIKE=""

log() {
  printf '\n[%s] %s\n' "install.sh" "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

run_root_cmd() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    echo "Root privileges are required to run: $*" >&2
    exit 1
  fi
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo "Python 3 is required but was not found." >&2
  exit 1
}

load_os_release() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    OS_ID="${ID:-}"
    OS_LIKE="${ID_LIKE:-}"
  fi
}

install_packages_apt() {
  run_root_cmd apt-get update
  run_root_cmd apt-get install -y python3 python3-venv python3-pip nodejs npm
}

install_packages_dnf() {
  run_root_cmd dnf install -y python3 python3-pip python3-virtualenv nodejs npm
}

install_packages_yum() {
  run_root_cmd yum install -y python3 python3-pip nodejs npm
}

ensure_prerequisites() {
  local missing=()
  command -v python3 >/dev/null 2>&1 || missing+=("python3")
  command -v npm >/dev/null 2>&1 || missing+=("npm")

  if [[ ${#missing[@]} -eq 0 ]]; then
    return
  fi

  log "Installing missing prerequisites: ${missing[*]}"
  load_os_release

  if command -v apt-get >/dev/null 2>&1 || [[ "$OS_ID" == "ubuntu" || "$OS_ID" == "debian" || "$OS_LIKE" == *"debian"* ]]; then
    install_packages_apt
    return
  fi

  if command -v dnf >/dev/null 2>&1 || [[ "$OS_LIKE" == *"fedora"* || "$OS_ID" == "fedora" ]]; then
    install_packages_dnf
    return
  fi

  if command -v yum >/dev/null 2>&1 || [[ "$OS_LIKE" == *"rhel"* || "$OS_ID" == "centos" ]]; then
    install_packages_yum
    return
  fi

  echo "Could not auto-install prerequisites on this Linux distribution." >&2
  echo "Please install Python 3, python3-venv, pip, Node.js, and npm manually, then rerun install.sh." >&2
  exit 1
}

ensure_prerequisites
PYTHON_CMD="$(find_python)"

log "Creating backend virtual environment"
"$PYTHON_CMD" -m venv "$VENV_DIR"

if [[ -x "$VENV_DIR/bin/python" ]]; then
  VENV_PYTHON="$VENV_DIR/bin/python"
  VENV_PIP="$VENV_DIR/bin/pip"
else
  echo "Virtual environment was created, but the expected Python binary was not found." >&2
  exit 1
fi

log "Upgrading pip"
"$VENV_PYTHON" -m pip install --upgrade pip

log "Installing backend dependencies"
"$VENV_PIP" install -r "$BACKEND_DIR/requirements.txt"

log "Installing frontend dependencies"
(
  cd "$FRONTEND_DIR"
  npm install
)

log "Building frontend"
(
  cd "$FRONTEND_DIR"
  VITE_API_URL=/api npm run build
)

log "Copying frontend build into backend static files"
rm -rf "$SPA_DIR"
mkdir -p "$SPA_DIR"
cp -R "$FRONTEND_DIR/dist/." "$SPA_DIR/"

log "Running Django migrations"
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" manage.py migrate
)

log "Seeding demo items"
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" manage.py seed_items
)

log "Collecting static files"
(
  cd "$BACKEND_DIR"
  "$VENV_PYTHON" manage.py collectstatic --noinput
)

if [[ ! -f "$ENV_FILE" ]]; then
  log "Creating backend environment file"
  cat > "$ENV_FILE" <<EOF
SECRET_KEY=change-this-secret-key
DEBUG=true
ALLOWED_HOSTS=127.0.0.1,localhost
SPA_ROOT=
DB_PATH=$BACKEND_DIR/db.sqlite3
EOF
fi

if [[ ! -f "$FRONTEND_ENV_FILE" ]]; then
  log "Creating frontend environment file"
  cat > "$FRONTEND_ENV_FILE" <<EOF
VITE_API_URL=/api
EOF
fi

cat <<EOF

Setup complete.

Backend virtualenv:
  $VENV_DIR

Environment file:
  $ENV_FILE

Frontend environment file:
  $FRONTEND_ENV_FILE

To run the backend manually:
  cd backend
  source venv/bin/activate
  gunicorn --bind 127.0.0.1:8000 --workers 2 --threads 2 config.wsgi:application

Open:
  http://localhost:8000
EOF
