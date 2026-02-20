#!/usr/bin/env bash
# ============================================================
# Financial Reasoning Eval Benchmark — Master Run Script
# ============================================================
# Usage:
#   ./run.sh              Run everything (setup → tests → eval → leaderboard)
#   ./run.sh setup        Install dependencies only
#   ./run.sh test         Run test suite only
#   ./run.sh generate     Regenerate benchmark dataset
#   ./run.sh eval [MODEL] Evaluate a model (auto-detects provider if omitted)
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

# ── Read a key value from .env ────────────────────────────
read_env_key() {
    local var_name="$1"
    if [[ -f "${REPO_DIR}/.env" ]]; then
        grep "^${var_name}=" "${REPO_DIR}/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" | xargs
    fi
}

# ── Check if a key is real (not empty / not a placeholder) ─
is_real_key() {
    local value="$1"
    [[ -n "${value}" && "${value}" != *"your-key-here"* && "${value}" != *"your_key_here"* ]]
}

# ── Check the API key required for a given model ─────────
check_api_key() {
    local model_lower
    model_lower=$(echo "$1" | tr '[:upper:]' '[:lower:]')

    # Ollama needs no API key
    if [[ "${model_lower}" == ollama:* ]]; then
        return 0
    fi

    local required_var=""
    if [[ "${model_lower}" == gpt* || "${model_lower}" == o1* || "${model_lower}" == o3* || "${model_lower}" == o4* ]]; then
        required_var="OPENAI_API_KEY"
    elif [[ "${model_lower}" == claude* ]]; then
        required_var="ANTHROPIC_API_KEY"
    else
        required_var="HF_API_KEY"
    fi

    local key_value
    key_value=$(read_env_key "${required_var}")

    if ! is_real_key "${key_value}"; then
        error "${required_var} is not configured. Edit .env before running eval with ${1}."
        exit 1
    fi
}

# ── Auto-detect available providers and select model ──────
select_model() {
    local providers=()
    local defaults=()

    # Check each provider's key in .env
    local anthropic_key openai_key hf_key
    anthropic_key=$(read_env_key "ANTHROPIC_API_KEY")
    openai_key=$(read_env_key "OPENAI_API_KEY")
    hf_key=$(read_env_key "HF_API_KEY")

    if is_real_key "${anthropic_key}"; then
        providers+=("Anthropic")
        defaults+=("claude-sonnet-4")
    fi
    if is_real_key "${openai_key}"; then
        providers+=("OpenAI")
        defaults+=("gpt-4.1")
    fi
    if is_real_key "${hf_key}"; then
        providers+=("HuggingFace")
        defaults+=("llama-3.3-70b")
    fi

    # Check for Ollama
    if curl -s --connect-timeout 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
        local first_ollama
        first_ollama=$(curl -s http://localhost:11434/api/tags 2>/dev/null | "${PYTHON}" -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    print(models[0]['name'])
" 2>/dev/null || true)
        if [[ -n "${first_ollama}" ]]; then
            providers+=("Ollama (local)")
            defaults+=("ollama:${first_ollama}")
        fi
    fi

    # Decision logic
    if [[ ${#providers[@]} -eq 0 ]]; then
        error "No API keys configured and Ollama is not running."
        error "Edit .env to add API keys, or start Ollama locally."
        exit 1
    elif [[ ${#providers[@]} -eq 1 ]]; then
        info "Auto-selected ${providers[0]} (only available provider)"
        echo "${defaults[0]}"
        return 0
    else
        echo "" >&2
        info "Multiple providers available:" >&2
        echo "" >&2
        for i in "${!providers[@]}"; do
            echo -e "  ${BOLD}$((i + 1)))${NC} ${providers[$i]}  →  ${defaults[$i]}" >&2
        done
        echo "" >&2

        local choice
        while true; do
            read -rp "$(echo -e "${BLUE}[?]${NC}  Select provider (1-${#providers[@]}): ")" choice
            if [[ "${choice}" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#providers[@]} )); then
                echo "${defaults[$((choice - 1))]}"
                return 0
            fi
            warn "Invalid choice. Enter a number between 1 and ${#providers[@]}." >&2
        done
    fi
}

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

    local model="${1:-}"
    local split="${2:-${DEFAULT_SPLIT}}"
    local limit="${3:-${DEFAULT_LIMIT}}"

    # If no model specified, auto-detect or prompt
    if [[ -z "${model}" ]]; then
        model=$(select_model)
        info "Selected model: ${model}"
    fi

    # Check that benchmark data exists
    if [[ ! -f "${DATA_DIR}/benchmark_${split}.json" ]]; then
        warn "Benchmark data not found — generating dataset first..."
        generate
    fi

    # Only check the API key needed for the selected model
    check_api_key "${model}"

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

# ── Compare models ─────────────────────────────────────────
compare() {
    header "Comparing models"

    if [[ ! -f "${PYTHON}" ]]; then
        error "Virtual environment not found. Run './run.sh setup' first."
        exit 1
    fi

    # Collect models from args (all args after "compare")
    local models=("$@")

    if [[ ${#models[@]} -lt 2 ]]; then
        error "Usage: ./run.sh compare MODEL1 MODEL2 [MODEL3 ...] [--limit N]"
        error "Example: ./run.sh compare claude-sonnet-4 ollama:llama3.2 --limit 20"
        exit 1
    fi

    # Parse out --limit if present
    local limit=""
    local clean_models=()
    local i=0
    while [[ $i -lt ${#models[@]} ]]; do
        if [[ "${models[$i]}" == "--limit" ]] && [[ $((i + 1)) -lt ${#models[@]} ]]; then
            limit="${models[$((i + 1))]}"
            i=$((i + 2))
        else
            clean_models+=("${models[$i]}")
            i=$((i + 1))
        fi
    done

    # Check API keys for each model
    for m in "${clean_models[@]}"; do
        check_api_key "${m}"
    done

    # Build command
    local cmd=("${PYTHON}" "${REPO_DIR}/scripts/compare_models.py"
        --models "${clean_models[@]}"
        --output-dir "${RESULTS_DIR}"
    )

    if [[ -n "${limit}" ]]; then
        cmd+=(--limit "${limit}")
    fi

    "${cmd[@]}"

    echo ""
    success "Comparison complete! Results saved to ${RESULTS_DIR}/"
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
    eval [MODEL] [SPLIT] [LIMIT]
                        Evaluate a model on the benchmark
                          MODEL  — model name or ollama:model (auto-detects if omitted)
                          SPLIT  — test | validation (default: test)
                          LIMIT  — max problems to evaluate (default: all)
    compare MODEL1 MODEL2 [... --limit N]
                        Compare multiple models side-by-side on the same problem set
    leaderboard         Launch the Gradio leaderboard UI
    help                Show this help message

EXAMPLES
    ./run.sh                                  # Full pipeline with defaults
    ./run.sh setup                            # Install deps only
    ./run.sh test                             # Run tests only
    ./run.sh eval                             # Auto-detect provider or choose interactively
    ./run.sh eval claude-sonnet-4             # Eval Claude Sonnet 4 on full test set
    ./run.sh eval gpt-4.1 test 50            # Eval GPT-4.1 on 50 test problems
    ./run.sh eval o3 test 20                  # Eval OpenAI o3 on 20 test problems
    ./run.sh eval claude-opus-4 validation    # Eval Claude Opus 4 on validation set
    ./run.sh eval llama-3.3-70b test 100      # Eval Llama 3.3 70B on 100 problems
    ./run.sh eval ollama:llama3.2 test 20     # Eval local Ollama model on 20 problems
    ./run.sh eval ollama:mistral test 10      # Eval local Mistral via Ollama
    ./run.sh compare claude-sonnet-4 ollama:llama3.2 --limit 20
                                              # Compare two models side-by-side
    ./run.sh generate 500                     # Generate 500 problems
    ./run.sh leaderboard                      # Launch Gradio UI

SUPPORTED MODELS
    Anthropic:    claude-opus-4, claude-sonnet-4, claude-haiku-3.5
    OpenAI:       gpt-4.1, gpt-4.1-mini, o3, o4-mini
    HuggingFace:  llama-4-scout, llama-3.3-70b, deepseek-r1, qwen2.5-72b
    Ollama:       ollama:llama3.2, ollama:mistral, ollama:phi3, ollama:deepseek-r1, ...
    Legacy:       claude-3.5-sonnet, gpt-4o, llama-3.1-70b, ...

ENVIRONMENT
    API keys are read from .env (copy .env.example to get started).
    Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or HF_API_KEY as needed.
    Only the key for your selected provider needs to be configured.

    Ollama models require no API key — just a running Ollama instance.
    Override the default Ollama URL with: OLLAMA_HOST=http://your-host:11434

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
            evaluate "${2:-}" "${3:-${DEFAULT_SPLIT}}" "${4:-${DEFAULT_LIMIT}}"
            ;;
        compare)
            shift  # remove "compare" from args
            compare "$@"
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
