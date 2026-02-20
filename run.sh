#!/usr/bin/env bash
# ============================================================
# Financial Reasoning Eval Benchmark — Master Run Script
# ============================================================
# Usage:
#   ./run.sh              Run everything (setup → tests → eval → leaderboard)
#   ./run.sh setup        Install dependencies only
#   ./run.sh test         Run test suite only
#   ./run.sh generate     Regenerate benchmark dataset
#   ./run.sh eval MODEL   Evaluate a specific model (default: claude-sonnet-4)
#   ./run.sh leaderboard  Launch the Gradio leaderboard UI
#   ./run.sh help         Show this help message
# ============================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_DIR}/venv"
DATA_DIR="${REPO_DIR}/data"
RESULTS_DIR="${REPO_DIR}/results"
PYTHON="${VENV_DIR}/bin/python3"

DEFAULT_MODEL="claude-sonnet-4"
DEFAULT_LIMIT=""           # empty = full test set
DEFAULT_SPLIT="test"

# ── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helpers ────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════${NC}"; \
            echo -e "${BOLD}${CYAN}  $*${NC}"; \
            echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════${NC}\n"; }

# ── Find best available Python ─────────────────────────────
find_python() {
    # Find a system Python 3.9+ (never use the venv python — it may be stale)
    local candidates=(
        python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3
    )

    for candidate in "${candidates[@]}"; do
        if command -v "${candidate}" &>/dev/null; then
            local ver
            ver=$("${candidate}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)

            if (( major >= 3 && minor >= 9 )); then
                SYSTEM_PYTHON="${candidate}"
                return 0
            fi
        fi
    done

    # Also check common Homebrew / system paths
    local paths=(
        /opt/homebrew/bin/python3
        /usr/local/bin/python3
        /usr/bin/python3
    )

    for p in "${paths[@]}"; do
        if [[ -x "${p}" ]]; then
            local ver
            ver=$("${p}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)

            if (( major >= 3 && minor >= 9 )); then
                SYSTEM_PYTHON="${p}"
                return 0
            fi
        fi
    done

    return 1
}

# ── Preflight checks ──────────────────────────────────────
preflight() {
    if ! find_python; then
        error "Python 3.9+ not found. Install Python and retry."
        exit 1
    fi

    local py_version
    py_version=$("${SYSTEM_PYTHON}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    success "Python ${py_version} detected (${SYSTEM_PYTHON})"
}

# ── Setup ──────────────────────────────────────────────────
setup() {
    header "Setting up environment"
    preflight

    # Create venv if missing, or recreate if broken (stale shebangs, moved paths, etc.)
    local need_venv=false
    if [[ ! -d "${VENV_DIR}" ]]; then
        need_venv=true
    elif ! "${PYTHON}" -c "import pip" &>/dev/null 2>&1; then
        warn "Existing venv is broken (stale paths?) — recreating..."
        rm -rf "${VENV_DIR}"
        need_venv=true
    fi

    if [[ "${need_venv}" == true ]]; then
        info "Creating virtual environment with ${SYSTEM_PYTHON}..."
        "${SYSTEM_PYTHON}" -m venv "${VENV_DIR}"
        success "Virtual environment created at ${VENV_DIR}"
    else
        success "Virtual environment already exists"
    fi

    # Upgrade pip (use python -m pip to avoid stale shebang issues)
    info "Upgrading pip..."
    "${PYTHON}" -m pip install --upgrade pip --quiet

    # Install dependencies
    info "Installing dependencies..."
    "${PYTHON}" -m pip install -r "${REPO_DIR}/requirements.txt" --quiet
    success "All dependencies installed"

    # Check for .env file
    if [[ ! -f "${REPO_DIR}/.env" ]]; then
        warn "No .env file found — copying from .env.example"
        cp "${REPO_DIR}/.env.example" "${REPO_DIR}/.env"
        warn "Edit .env and add your API keys before running evaluations"
    else
        success ".env file found"
    fi

    # Verify API keys are configured (not just placeholders)
    if grep -q "your-key-here" "${REPO_DIR}/.env" 2>/dev/null; then
        warn "API keys in .env still contain placeholders — update before running eval"
    fi

    # Create results directory
    mkdir -p "${RESULTS_DIR}"

    echo ""
    success "Setup complete!"
}

# ── Tests ──────────────────────────────────────────────────
run_tests() {
    header "Running test suite"

    if [[ ! -f "${PYTHON}" ]]; then
        error "Virtual environment not found. Run './run.sh setup' first."
        exit 1
    fi

    info "Running benchmark tests..."
    "${PYTHON}" "${REPO_DIR}/scripts/test_benchmark.py"

    echo ""
    success "All tests passed!"
}

# ── Dataset generation ─────────────────────────────────────
generate() {
    header "Generating benchmark dataset"

    if [[ ! -f "${PYTHON}" ]]; then
        error "Virtual environment not found. Run './run.sh setup' first."
        exit 1
    fi

    local num_problems="${1:-300}"

    info "Generating ${num_problems} problems..."
    "${PYTHON}" "${REPO_DIR}/scripts/generate_dataset.py" \
        --output-dir "${DATA_DIR}" \
        --num-problems "${num_problems}" \
        --seed 42 \
        --huggingface-format

    # Add advanced problems
    info "Merging advanced curated problems..."
    "${PYTHON}" "${REPO_DIR}/scripts/add_advanced_problems.py"

    echo ""
    success "Dataset generation complete!"
    info "Files written to ${DATA_DIR}/"
}

# ── Evaluation ─────────────────────────────────────────────
evaluate() {
    header "Running model evaluation"

    if [[ ! -f "${PYTHON}" ]]; then
        error "Virtual environment not found. Run './run.sh setup' first."
        exit 1
    fi

    local model="${1:-${DEFAULT_MODEL}}"
    local split="${2:-${DEFAULT_SPLIT}}"
    local limit="${3:-${DEFAULT_LIMIT}}"

    # Check that benchmark data exists
    if [[ ! -f "${DATA_DIR}/benchmark_${split}.json" ]]; then
        warn "Benchmark data not found — generating dataset first..."
        generate
    fi

    # Check API keys
    if [[ -f "${REPO_DIR}/.env" ]] && grep -q "your-key-here" "${REPO_DIR}/.env" 2>/dev/null; then
        error "API keys in .env still contain placeholders. Edit .env before running eval."
        exit 1
    fi

    info "Model:  ${model}"
    info "Split:  ${split}"
    if [[ -n "${limit}" ]]; then
        info "Limit:  ${limit} problems"
    else
        info "Limit:  full test set"
    fi

    echo ""

    # Build command
    local cmd=("${PYTHON}" "${REPO_DIR}/runners/run_evaluation.py"
        --model "${model}"
        --split "${split}"
        --output-dir "${RESULTS_DIR}"
    )

    if [[ -n "${limit}" ]]; then
        cmd+=(--limit "${limit}")
    fi

    "${cmd[@]}"

    echo ""
    success "Evaluation complete! Results saved to ${RESULTS_DIR}/"
}

# ── Leaderboard ────────────────────────────────────────────
leaderboard() {
    header "Launching leaderboard UI"

    if [[ ! -f "${PYTHON}" ]]; then
        error "Virtual environment not found. Run './run.sh setup' first."
        exit 1
    fi

    info "Starting Gradio app..."
    info "Press Ctrl+C to stop"
    echo ""

    "${PYTHON}" "${REPO_DIR}/spaces/app.py"
}

# ── Run everything ─────────────────────────────────────────
run_all() {
    header "Financial Reasoning Eval Benchmark"
    info "Running full pipeline: setup → test → eval"
    echo ""

    setup
    run_tests
    evaluate "${DEFAULT_MODEL}" "${DEFAULT_SPLIT}" "${DEFAULT_LIMIT}"

    header "All done!"
    info "Results:     ${RESULTS_DIR}/"
    info "Data:        ${DATA_DIR}/"
    info "Leaderboard: ./run.sh leaderboard"
}

# ── Help ───────────────────────────────────────────────────
show_help() {
    cat <<'HELP'

Financial Reasoning Eval Benchmark — Run Script
────────────────────────────────────────────────

USAGE
    ./run.sh [command] [options]

COMMANDS
    (none)              Run full pipeline (setup → tests → eval)
    setup               Create venv and install dependencies
    test                Run the test suite
    generate [N]        Regenerate benchmark dataset (default: 300 problems)
    eval MODEL [SPLIT] [LIMIT]
                        Evaluate a model on the benchmark
                          MODEL  — model name (default: claude-sonnet-4)
                          SPLIT  — test | validation (default: test)
                          LIMIT  — max problems to evaluate (default: all)
    leaderboard         Launch the Gradio leaderboard UI
    help                Show this help message

EXAMPLES
    ./run.sh                                  # Full pipeline with defaults
    ./run.sh setup                            # Install deps only
    ./run.sh test                             # Run tests only
    ./run.sh eval claude-sonnet-4             # Eval Claude Sonnet 4 on full test set
    ./run.sh eval gpt-4.1 test 50            # Eval GPT-4.1 on 50 test problems
    ./run.sh eval o3 test 20                  # Eval OpenAI o3 on 20 test problems
    ./run.sh eval claude-opus-4 validation    # Eval Claude Opus 4 on validation set
    ./run.sh eval llama-3.3-70b test 100      # Eval Llama 3.3 70B on 100 problems
    ./run.sh generate 500                     # Generate 500 problems
    ./run.sh leaderboard                      # Launch Gradio UI

SUPPORTED MODELS
    Anthropic:    claude-opus-4, claude-sonnet-4, claude-haiku-3.5
    OpenAI:       gpt-4.1, gpt-4.1-mini, o3, o4-mini
    HuggingFace:  llama-4-scout, llama-3.3-70b, deepseek-r1, qwen2.5-72b
    Legacy:       claude-3.5-sonnet, gpt-4o, llama-3.1-70b, ...

ENVIRONMENT
    API keys are read from .env (copy .env.example to get started).
    Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or HF_API_KEY as needed.

HELP
}

# ── Main dispatch ──────────────────────────────────────────
main() {
    local command="${1:-}"

    case "${command}" in
        setup)
            setup
            ;;
        test|tests)
            run_tests
            ;;
        generate|gen)
            generate "${2:-300}"
            ;;
        eval|evaluate)
            evaluate "${2:-${DEFAULT_MODEL}}" "${3:-${DEFAULT_SPLIT}}" "${4:-${DEFAULT_LIMIT}}"
            ;;
        leaderboard|ui)
            leaderboard
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            run_all
            ;;
        *)
            error "Unknown command: ${command}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
