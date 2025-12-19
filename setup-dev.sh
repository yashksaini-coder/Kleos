#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info()    { echo -e "${GREEN}[INFO] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
print_error()   { echo -e "${RED}[ERROR] $1${NC}"; }

print_info "Starting Kleos CLI development setup..."

# ---------------------------
# Python Version Check
# ---------------------------
PYTHON=$(command -v python3 || command -v python)
if [[ -z "$PYTHON" ]]; then
    print_error "Python 3 is not installed or not in PATH. Please install Python 3.8+."
    exit 1
fi

PY_VERSION=$($PYTHON -V 2>&1 | grep -Po '(?<=Python )(.+)')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    print_error "Python $PY_VERSION found. Kleos requires Python 3.8 or higher."
    exit 1
else
    print_info "Python $PY_VERSION found."
fi

# ---------------------------
# pip Check
# ---------------------------
if ! command -v uv pip &>/dev/null && ! command -v python -m pip &>/dev/null; then
    print_error "pip is not installed. Please install pip."
    exit 1
else
    print_info "pip found."
fi

# ---------------------------
# Virtual Environment
# ---------------------------
VENV_DIR=".venv"
DEFAULT_CREATE_VENV="yes"

read -r -p "Create and use a Python virtual environment in ${VENV_DIR}? (yes/no) [${DEFAULT_CREATE_VENV}]: " CREATE_VENV
CREATE_VENV=${CREATE_VENV:-${DEFAULT_CREATE_VENV}}

if [[ "$CREATE_VENV" == "yes" ]]; then
    if [ -d "$VENV_DIR" ]; then
        print_info "Virtual environment ${VENV_DIR} already exists."
    else
        print_info "Creating virtual environment..."
        $PYTHON -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment."
            exit 1
        fi
    fi

    print_info "Activating virtual environment..."
    # Support both Linux/macOS and Git Bash on Windows
    ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
    [[ ! -f "$ACTIVATE_SCRIPT" ]] && ACTIVATE_SCRIPT="${VENV_DIR}/Scripts/activate"

    # shellcheck disable=SC1090
    source "$ACTIVATE_SCRIPT" || {
        print_error "Failed to activate virtual environment. Please run: source $ACTIVATE_SCRIPT"
    }

else
    print_warning "Skipping virtual environment. Dependencies will be installed globally."
    read -r -p "Proceed with global installation? (yes/no) [no]: " CONFIRM_GLOBAL
    CONFIRM_GLOBAL=${CONFIRM_GLOBAL:-no}
    [[ "$CONFIRM_GLOBAL" != "yes" ]] && {
        print_info "Aborted by user."
        exit 0
    }
fi

# ---------------------------
# Install Kleos CLI
# ---------------------------
print_info "Installing Kleos CLI..."
uv pip install . || {
    print_error "Failed to install Kleos CLI."
    exit 1
}

# ---------------------------
# Success Message
# ---------------------------
print_info "✅ Kleos CLI setup complete!"
echo
print_info "To activate the virtual environment again later:"
if [[ "$CREATE_VENV" == "yes" ]]; then
    print_info "  source ${VENV_DIR}/bin/activate  (or ${VENV_DIR}/Scripts/activate on Windows)"
fi
print_info "Then run:"
print_info "  kleos --help"
echo

exit 0
