#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.local/bin"
cat << WRAPPER > "$HOME/.local/bin/view"
#!/usr/bin/env bash
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/view.py" "\$@"
WRAPPER
chmod +x "$HOME/.local/bin/view"
echo "VIEW CLI wrapper installed at $HOME/.local/bin/view"
