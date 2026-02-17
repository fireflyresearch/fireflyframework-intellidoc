#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# fireflyframework-intellidoc installer
# Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── TTY detection (curl | bash support) ──────────────────────────────────────
if [ ! -t 0 ]; then
    exec < /dev/tty
fi

# ── Color codes ──────────────────────────────────────────────────────────────
if [ -n "${NO_COLOR:-}" ]; then
    DIM="" RESET=""
    RED="" GREEN="" YELLOW="" BLUE="" CYAN="" WHITE=""
else
    DIM="\033[2m"  RESET="\033[0m"
    RED="\033[1;31m"  GREEN="\033[1;32m"  YELLOW="\033[1;33m"
    BLUE="\033[1;34m"  CYAN="\033[1;36m"  WHITE="\033[1;37m"
fi

VERSION="26.02.01"

# ── Helpers ──────────────────────────────────────────────────────────────────

print_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${CYAN}  $1${RESET}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
}

print_success() { echo -e "  ${GREEN}✓${RESET} $1"; }
print_error()   { echo -e "  ${RED}✗${RESET} $1"; }
print_warn()    { echo -e "  ${YELLOW}!${RESET} $1"; }
print_info()    { echo -e "  ${BLUE}→${RESET} $1"; }

prompt_choice() {
    local prompt="$1"
    shift
    local options=("$@")
    echo ""
    echo -e "  ${WHITE}${prompt}${RESET}"
    echo ""
    for i in "${!options[@]}"; do
        echo -e "    ${CYAN}$((i + 1)))${RESET} ${options[$i]}"
    done
    echo ""
    while true; do
        read -rp "  Enter choice [1-${#options[@]}]: " choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            CHOICE_RESULT=$choice
            return
        fi
        echo -e "  ${RED}Invalid choice. Please enter 1-${#options[@]}.${RESET}"
    done
}

prompt_input() {
    local prompt="$1"
    local default="${2:-}"
    if [ -n "$default" ]; then
        read -rp "  ${prompt} [${default}]: " value
        echo "${value:-$default}"
    else
        read -rp "  ${prompt}: " value
        echo "$value"
    fi
}

prompt_secret() {
    local prompt="$1"
    read -rsp "  ${prompt}: " value
    echo ""
    echo "$value"
}

prompt_confirm() {
    local prompt="$1"
    local default="${2:-y}"
    if [ "$default" = "y" ]; then
        read -rp "  ${prompt} [Y/n]: " yn
        yn="${yn:-y}"
    else
        read -rp "  ${prompt} [y/N]: " yn
        yn="${yn:-n}"
    fi
    [[ "$yn" =~ ^[Yy] ]]
}

# ── Cleanup trap ─────────────────────────────────────────────────────────────
cleanup() {
    if [ $? -ne 0 ]; then
        echo ""
        print_error "Installation failed. Check the output above for details."
    fi
}
trap cleanup EXIT

# ── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}"
cat << 'BANNER'
    ___       __       ____  _ ____
   /   |___  / /____  / / / (_) __ \____  _____
  / /| / __ \/ __/ _ \/ / / / / / / / __ \/ ___/
 / ___ / / / / /_/  __/ / / / / /_/ / /_/ / /__
/_/  |_/_/ /_/\__/\___/_/_/ /_/_____/\____/\___/
BANNER
echo -e "${RESET}"
echo -e "  ${DIM}Copyright 2026 Firefly Software Solutions Inc${RESET}"
echo -e "  ${DIM}Apache License 2.0 — v${VERSION}${RESET}"
echo ""
echo -e "  ${WHITE}Intelligent Document Processing powered by Vision-Language Models${RESET}"

# ══════════════════════════════════════════════════════════════════════════════
# Step 1: System Prerequisites
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 1 / 10 — System Prerequisites"

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Darwin*)  OS="macos";;
    Linux*)
        if grep -qi microsoft /proc/version 2>/dev/null; then
            OS="wsl"
        else
            OS="linux"
        fi
        ;;
esac
print_info "Detected OS: ${OS}"

# Python check
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    print_error "Python not found. Please install Python 3.13+ first."
    case "$OS" in
        macos) print_info "  brew install python@3.13" ;;
        linux|wsl) print_info "  sudo apt install python3.13  OR  sudo dnf install python3.13" ;;
    esac
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 13 ]; }; then
    print_error "Python >= 3.13 required (found ${PYTHON_VERSION})"
    exit 1
fi
print_success "Python ${PYTHON_VERSION}"

# uv check
USE_UV=false
if command -v uv &>/dev/null; then
    UV_VERSION=$(uv --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    print_success "uv ${UV_VERSION}"
    USE_UV=true
else
    print_warn "uv not found"
    if prompt_confirm "Install uv (recommended package manager)?"; then
        print_info "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv &>/dev/null; then
            print_success "uv installed"
            USE_UV=true
        else
            print_warn "uv installation failed — falling back to pip"
        fi
    else
        print_info "Continuing with pip"
    fi
fi

# pip check (fallback)
if [ "$USE_UV" = false ]; then
    if $PYTHON_CMD -m pip --version &>/dev/null; then
        PIP_VERSION=$($PYTHON_CMD -m pip --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        print_success "pip ${PIP_VERSION}"
    else
        print_error "Neither uv nor pip found. Cannot install packages."
        exit 1
    fi
fi

# git check
if command -v git &>/dev/null; then
    GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    print_success "git ${GIT_VERSION}"
else
    print_warn "git not found (needed to clone from GitHub)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 2: Source Detection
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 2 / 10 — Source Detection"

SOURCE_MODE=""
SOURCE_DIR=""

# Check CWD and parent for local source
for dir in "." ".."; do
    if [ -f "${dir}/pyproject.toml" ] && grep -q "fireflyframework-intellidoc" "${dir}/pyproject.toml" 2>/dev/null; then
        SOURCE_DIR="$(cd "$dir" && pwd)"
        SOURCE_MODE="local"
        break
    fi
done

if [ "$SOURCE_MODE" = "local" ]; then
    print_success "Found local source: ${SOURCE_DIR}"
    print_info "Will install from local source"
else
    print_info "No local source found"
    prompt_choice "How would you like to install?" \
        "Clone from GitHub (full source)" \
        "Install from PyPI (package only)"

    if [ "$CHOICE_RESULT" -eq 1 ]; then
        SOURCE_MODE="github"
        if ! command -v git &>/dev/null; then
            print_error "git is required to clone from GitHub"
            exit 1
        fi
    else
        SOURCE_MODE="pypi"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 3: Installation Profile
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 3 / 10 — Installation Profile"

EXTRAS=""

prompt_choice "Select an installation profile:" \
    "Minimal — core + web server" \
    "Standard — core + cloud storage + observability" \
    "Full — all extras" \
    "Custom — choose individual extras"

case "$CHOICE_RESULT" in
    1) EXTRAS="web" ;;
    2) EXTRAS="web,s3,observability" ;;
    3) EXTRAS="all" ;;
    4)
        EXTRAS=""
        echo ""
        echo -e "  ${WHITE}Select extras (enter numbers separated by spaces):${RESET}"
        echo ""

        EXTRA_NAMES=("web" "pdf-images" "ocr" "barcode" "s3" "azure" "gcs" "postgresql" "mongodb" "messaging" "observability" "security")
        EXTRA_DESCS=(
            "Web server (Starlette/Uvicorn)"
            "PDF to image conversion (requires poppler)"
            "OCR fallback via pytesseract"
            "Barcode/QR code detection"
            "Amazon S3 storage"
            "Azure Blob Storage"
            "Google Cloud Storage"
            "PostgreSQL persistence"
            "MongoDB persistence"
            "Kafka/RabbitMQ messaging"
            "Prometheus metrics & tracing"
            "Authentication & RBAC"
        )

        for i in "${!EXTRA_NAMES[@]}"; do
            printf "    ${CYAN}%2d)${RESET} %-16s ${DIM}%s${RESET}\n" "$((i + 1))" "${EXTRA_NAMES[$i]}" "${EXTRA_DESCS[$i]}"
        done

        echo ""
        read -rp "  Enter numbers (e.g. 1 2 5 11): " selections

        SELECTED_EXTRAS=()
        for sel in $selections; do
            if [[ "$sel" =~ ^[0-9]+$ ]] && [ "$sel" -ge 1 ] && [ "$sel" -le "${#EXTRA_NAMES[@]}" ]; then
                SELECTED_EXTRAS+=("${EXTRA_NAMES[$((sel - 1))]}")
            fi
        done

        if [ ${#SELECTED_EXTRAS[@]} -eq 0 ]; then
            print_warn "No extras selected — installing core only"
            EXTRAS=""
        else
            EXTRAS=$(IFS=,; echo "${SELECTED_EXTRAS[*]}")
        fi
        ;;
esac

if [ -n "$EXTRAS" ]; then
    print_success "Extras: ${EXTRAS}"
else
    print_info "Core only (no extras)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 4: System Dependencies Check
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 4 / 10 — System Dependencies"

MISSING_DEPS=()

# Check poppler (needed by pdf-images)
if [[ "$EXTRAS" == *"pdf-images"* ]] || [[ "$EXTRAS" == "all" ]]; then
    if command -v pdftoppm &>/dev/null; then
        print_success "poppler (pdftoppm) found"
    else
        print_warn "poppler not found (required by pdf-images extra)"
        MISSING_DEPS+=("poppler")
        case "$OS" in
            macos)   print_info "  Install: brew install poppler" ;;
            linux)   print_info "  Install: sudo apt install poppler-utils" ;;
            wsl)     print_info "  Install: sudo apt install poppler-utils" ;;
        esac
    fi
fi

# Check tesseract (needed by ocr)
if [[ "$EXTRAS" == *"ocr"* ]] || [[ "$EXTRAS" == "all" ]]; then
    if command -v tesseract &>/dev/null; then
        print_success "tesseract found"
    else
        print_warn "tesseract not found (required by ocr extra)"
        MISSING_DEPS+=("tesseract")
        case "$OS" in
            macos)   print_info "  Install: brew install tesseract" ;;
            linux)   print_info "  Install: sudo apt install tesseract-ocr" ;;
            wsl)     print_info "  Install: sudo apt install tesseract-ocr" ;;
        esac
    fi
fi

# Check zbar (needed by barcode)
if [[ "$EXTRAS" == *"barcode"* ]] || [[ "$EXTRAS" == "all" ]]; then
    if command -v zbarimg &>/dev/null || ldconfig -p 2>/dev/null | grep -q libzbar; then
        print_success "zbar found"
    else
        print_warn "zbar not found (required by barcode extra)"
        MISSING_DEPS+=("zbar")
        case "$OS" in
            macos)   print_info "  Install: brew install zbar" ;;
            linux)   print_info "  Install: sudo apt install libzbar0" ;;
            wsl)     print_info "  Install: sudo apt install libzbar0" ;;
        esac
    fi
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    if ! prompt_confirm "Continue without installing system dependencies?"; then
        print_info "Install the dependencies above, then re-run this installer."
        exit 0
    fi
else
    print_success "All system dependencies satisfied"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 5: VLM Provider Selection
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 5 / 10 — VLM Provider"

prompt_choice "Select your VLM provider:" \
    "OpenAI (gpt-4o) — recommended" \
    "Anthropic (claude-sonnet-4-5-20250929)" \
    "Google (gemini-2.0-flash)"

case "$CHOICE_RESULT" in
    1)
        VLM_PROVIDER="openai"
        VLM_MODEL="openai:gpt-4o"
        VLM_ENV_VAR="OPENAI_API_KEY"
        ;;
    2)
        VLM_PROVIDER="anthropic"
        VLM_MODEL="anthropic:claude-sonnet-4-5-20250929"
        VLM_ENV_VAR="ANTHROPIC_API_KEY"
        ;;
    3)
        VLM_PROVIDER="google"
        VLM_MODEL="google:gemini-2.0-flash"
        VLM_ENV_VAR="GOOGLE_API_KEY"
        ;;
esac

print_success "Provider: ${VLM_PROVIDER} (${VLM_MODEL})"
echo ""

# Check for existing key in environment
EXISTING_KEY="${!VLM_ENV_VAR:-}"
if [ -n "$EXISTING_KEY" ]; then
    MASKED="${EXISTING_KEY:0:8}...${EXISTING_KEY: -4}"
    print_info "Found existing ${VLM_ENV_VAR}: ${MASKED}"
    if prompt_confirm "Use this key?"; then
        API_KEY="$EXISTING_KEY"
    else
        API_KEY=$(prompt_secret "Enter your ${VLM_ENV_VAR}")
    fi
else
    API_KEY=$(prompt_secret "Enter your ${VLM_ENV_VAR}")
fi

if [ -z "$API_KEY" ]; then
    print_warn "No API key provided — you can set ${VLM_ENV_VAR} in .env later"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 6: Storage Backend
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 6 / 10 — Storage Backend"

prompt_choice "Select document storage backend:" \
    "Local filesystem (default)" \
    "Amazon S3" \
    "Azure Blob Storage" \
    "Google Cloud Storage"

STORAGE_PROVIDER="local"

case "$CHOICE_RESULT" in
    1)
        STORAGE_PROVIDER="local"
        STORAGE_LOCAL_PATH=$(prompt_input "Storage directory" "./intellidoc-storage")
        ;;
    2)
        STORAGE_PROVIDER="s3"
        S3_BUCKET=$(prompt_input "S3 bucket name" "")
        S3_REGION=$(prompt_input "AWS region" "us-east-1")
        S3_ACCESS_KEY=$(prompt_input "AWS access key ID (or leave empty for IAM role)" "")
        if [ -n "$S3_ACCESS_KEY" ]; then
            S3_SECRET_KEY=$(prompt_secret "AWS secret access key")
        fi
        ;;
    3)
        STORAGE_PROVIDER="azure_blob"
        AZURE_CONTAINER=$(prompt_input "Azure container name" "")
        AZURE_CONNECTION=$(prompt_secret "Azure connection string")
        ;;
    4)
        STORAGE_PROVIDER="gcs"
        GCS_BUCKET=$(prompt_input "GCS bucket name" "")
        GCS_PROJECT=$(prompt_input "GCP project ID" "")
        ;;
esac

print_success "Storage: ${STORAGE_PROVIDER}"

# ══════════════════════════════════════════════════════════════════════════════
# Step 7: Port & Project Name
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 7 / 10 — Project Settings"

PROJECT_DIR=$(prompt_input "Project directory name" "intellidoc-service")
WEB_PORT=$(prompt_input "Web server port" "8080")

print_success "Project: ${PROJECT_DIR}"
print_success "Port: ${WEB_PORT}"

# ══════════════════════════════════════════════════════════════════════════════
# Step 8: Install
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 8 / 10 — Installing"

# Create project directory
if [ -d "$PROJECT_DIR" ]; then
    print_warn "Directory ${PROJECT_DIR} already exists"
    if ! prompt_confirm "Continue and overwrite config files?"; then
        exit 0
    fi
else
    mkdir -p "$PROJECT_DIR"
    print_success "Created ${PROJECT_DIR}/"
fi

cd "$PROJECT_DIR"

# Create virtual environment
print_info "Creating virtual environment..."
if [ "$USE_UV" = true ]; then
    uv venv .venv --python "$PYTHON_CMD" -q
else
    $PYTHON_CMD -m venv .venv
fi
print_success "Virtual environment created"

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install package
INSTALL_SPEC="fireflyframework-intellidoc"
if [ -n "$EXTRAS" ]; then
    INSTALL_SPEC="fireflyframework-intellidoc[${EXTRAS}]"
fi

print_info "Installing ${INSTALL_SPEC}..."

case "$SOURCE_MODE" in
    local)
        if [ "$USE_UV" = true ]; then
            uv pip install -e "${SOURCE_DIR}[${EXTRAS:-}]" -q
        else
            $PYTHON_CMD -m pip install -e "${SOURCE_DIR}[${EXTRAS:-}]" -q
        fi
        ;;
    github)
        git clone --depth 1 https://github.com/fireflyframework/fireflyframework-intellidoc.git _src -q 2>/dev/null || true
        if [ "$USE_UV" = true ]; then
            uv pip install -e "./_src[${EXTRAS:-}]" -q
        else
            $PYTHON_CMD -m pip install -e "./_src[${EXTRAS:-}]" -q
        fi
        ;;
    pypi)
        if [ "$USE_UV" = true ]; then
            uv pip install "${INSTALL_SPEC}" -q
        else
            $PYTHON_CMD -m pip install "${INSTALL_SPEC}" -q
        fi
        ;;
esac

print_success "Package installed"

# ── Generate pyfly.yaml ─────────────────────────────────────────────────────
print_info "Generating pyfly.yaml..."

cat > pyfly.yaml << YAML
pyfly:
  app:
    module: fireflyframework_intellidoc.main:app

  server:
    port: ${WEB_PORT}

  intellidoc:
    enabled: true
    default_model: "${VLM_MODEL}"
    storage_provider: "${STORAGE_PROVIDER}"
YAML

# Add storage-specific config
case "$STORAGE_PROVIDER" in
    local)
        cat >> pyfly.yaml << YAML
    storage_local_path: "${STORAGE_LOCAL_PATH}"
YAML
        ;;
    s3)
        cat >> pyfly.yaml << YAML
    storage_s3_bucket: "${S3_BUCKET}"
    storage_s3_region: "${S3_REGION}"
YAML
        ;;
    azure_blob)
        cat >> pyfly.yaml << YAML
    storage_azure_container: "${AZURE_CONTAINER}"
YAML
        ;;
    gcs)
        cat >> pyfly.yaml << YAML
    storage_gcs_bucket: "${GCS_BUCKET}"
    storage_gcs_project: "${GCS_PROJECT}"
YAML
        ;;
esac

print_success "Generated pyfly.yaml"

# ── Generate .env ────────────────────────────────────────────────────────────
print_info "Generating .env..."

{
    echo "# IntelliDoc environment — generated by install.sh"
    echo ""
    if [ -n "$API_KEY" ]; then
        echo "${VLM_ENV_VAR}=${API_KEY}"
    else
        echo "# ${VLM_ENV_VAR}=your-api-key-here"
    fi
    echo ""

    # Cloud storage credentials
    case "$STORAGE_PROVIDER" in
        s3)
            if [ -n "${S3_ACCESS_KEY:-}" ]; then
                echo "AWS_ACCESS_KEY_ID=${S3_ACCESS_KEY}"
                echo "AWS_SECRET_ACCESS_KEY=${S3_SECRET_KEY}"
            fi
            ;;
        azure_blob)
            echo "AZURE_STORAGE_CONNECTION_STRING=${AZURE_CONNECTION}"
            ;;
    esac
} > .env

chmod 600 .env
print_success "Generated .env (permissions: 600)"

# ── Create local storage directory ───────────────────────────────────────────
if [ "$STORAGE_PROVIDER" = "local" ]; then
    mkdir -p "${STORAGE_LOCAL_PATH}"
    print_success "Created ${STORAGE_LOCAL_PATH}/"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 9: Verification
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 9 / 10 — Verification"

if prompt_confirm "Run a quick health check? (starts and stops the service)"; then
    print_info "Starting service..."
    pyfly run &
    SERVICE_PID=$!

    # Wait for startup
    RETRIES=0
    HEALTH_OK=false
    while [ $RETRIES -lt 15 ]; do
        sleep 2
        if curl -sf "http://localhost:${WEB_PORT}/api/v1/intellidoc/health" >/dev/null 2>&1; then
            HEALTH_OK=true
            break
        fi
        RETRIES=$((RETRIES + 1))
    done

    if [ "$HEALTH_OK" = true ]; then
        print_success "Health check passed"
    else
        print_warn "Health check timed out — service may need more time to start"
    fi

    # Stop service
    kill "$SERVICE_PID" 2>/dev/null || true
    wait "$SERVICE_PID" 2>/dev/null || true
    print_info "Service stopped"
else
    print_info "Skipped — verify manually with: pyfly run"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Step 10: Summary
# ══════════════════════════════════════════════════════════════════════════════
print_step "Step 10 / 10 — Done!"

echo -e "${GREEN}"
cat << 'DONE'
  ┌──────────────────────────────────────────────────────────────┐
  │                  Installation Complete!                       │
  └──────────────────────────────────────────────────────────────┘
DONE
echo -e "${RESET}"

echo -e "  ${WHITE}Summary${RESET}"
echo -e "  ${DIM}────────────────────────────────────────${RESET}"
echo -e "  Project directory:  ${CYAN}$(pwd)${RESET}"
echo -e "  Extras:             ${CYAN}${EXTRAS:-core only}${RESET}"
echo -e "  VLM provider:       ${CYAN}${VLM_PROVIDER} (${VLM_MODEL})${RESET}"
echo -e "  Storage:            ${CYAN}${STORAGE_PROVIDER}${RESET}"
echo -e "  Port:               ${CYAN}${WEB_PORT}${RESET}"
echo -e "  Config:             ${CYAN}pyfly.yaml${RESET}"
echo -e "  Secrets:            ${CYAN}.env${RESET}"
echo ""
echo -e "  ${WHITE}Next Steps${RESET}"
echo -e "  ${DIM}────────────────────────────────────────${RESET}"
echo -e "  ${GREEN}1.${RESET} cd ${PROJECT_DIR}"
echo -e "  ${GREEN}2.${RESET} source .venv/bin/activate"
echo -e "  ${GREEN}3.${RESET} pyfly run"
echo ""
echo -e "  ${DIM}Health:${RESET}    http://localhost:${WEB_PORT}/api/v1/intellidoc/health"
echo -e "  ${DIM}API Docs:${RESET}  http://localhost:${WEB_PORT}/docs"
echo ""
