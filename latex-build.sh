#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DOCUMENT="${1:-$ROOT/论文/article_skycausal_v2.tex}"
ENGINE="${2:-pdf}"

case "$DOCUMENT" in
    "$ROOT"/*) RELATIVE_DOCUMENT="${DOCUMENT#"$ROOT"/}" ;;
    /*)
        printf 'Document must be inside the workspace: %s\n' "$DOCUMENT" >&2
        exit 2
        ;;
    *) RELATIVE_DOCUMENT="$DOCUMENT" ;;
esac

DOCUMENT_DIR="$(dirname -- "$RELATIVE_DOCUMENT")"
DOCUMENT_FILE="$(basename -- "$RELATIVE_DOCUMENT")"
HOST_OUTPUT_DIR="$ROOT/$DOCUMENT_DIR/build"
CONTAINER_WORKDIR="/workspace/$DOCUMENT_DIR"

case "$ENGINE" in
    pdf) LATEXMK_MODE="-pdf" ;;
    xelatex) LATEXMK_MODE="-xelatex" ;;
    clean) LATEXMK_MODE="-C" ;;
    *)
        printf 'Unknown mode "%s"; use pdf, xelatex, or clean.\n' "$ENGINE" >&2
        exit 2
        ;;
esac

mkdir -p "$HOST_OUTPUT_DIR"
export LATEX_UID="$(id -u)"
export LATEX_GID="$(id -g)"

docker compose \
    -f "$ROOT/compose.latex.yaml" \
    run --rm \
    --workdir "$CONTAINER_WORKDIR" \
    latex \
    latexmk \
    "$LATEXMK_MODE" \
    -interaction=nonstopmode \
    -file-line-error \
    -synctex=1 \
    -outdir=build \
    "$DOCUMENT_FILE"
