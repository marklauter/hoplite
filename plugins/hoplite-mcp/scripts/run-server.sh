#!/bin/sh
# Launcher for the catalog MCP server. Probes the configured interpreter first, because
# a broken one (missing, or the Windows Store stub) would fail before the server could
# ever explain itself. Stdout carries JSON-RPC, so every message here goes to stderr.
PY="${CLAUDE_PLUGIN_OPTION_PYTHON_PATH:-python3}"
"$PY" -c "" 2>/dev/null || {
  echo "hoplite-mcp: '$PY' is not a working Python. Tell the user to set the plugin's 'Python executable' (python_path) option — re-enable the plugin or edit pluginConfigs in settings.json — and then run /reload-plugins (or restart the session) so the new value takes effect. Only the user can do this; the agent cannot reload plugins. On Windows, 'python' or a full path usually works." >&2
  exit 2
}
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH
exec "$PY" -m hoplite_catalog.server
