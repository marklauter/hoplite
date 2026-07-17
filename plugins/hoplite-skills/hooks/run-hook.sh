#!/bin/sh
# Launcher for check-frontmatter.py. Probes the configured interpreter first,
# because a broken one (missing, or the Windows Store stub) fails before the
# script could ever explain itself.
PY="${CLAUDE_PLUGIN_OPTION_PYTHON_PATH:-python3}"
"$PY" -c "" 2>/dev/null || {
  echo "hoplite-skills: '$PY' is not a working Python. Set the plugin's 'Python executable' (python_path) option — re-enable the plugin or edit pluginConfigs in settings.json. On Windows, try 'python' or a full path." >&2
  exit 2
}
exec "$PY" "${CLAUDE_PLUGIN_ROOT}/hooks/check-frontmatter.py"
