# Keep a separate bash history file for each JetBrains project.
#
# Source this from ~/.bashrc. Relies on PROJECT_NAME being exported per
# project (e.g. via the IDE's terminal environment variables).
#
# Inspired by https://intellij-support.jetbrains.com/hc/en-us/community/posts/16588850105106-Seperate-shell-history-for-each-terminal-window?page=1#community_comment_19712074173074

cleanStr () {
    local a=${1//[^[:alnum:]]/-}
    echo "${a,,}"
}

# Detect if the terminal is a JetBrains terminal
if [[ "$TERMINAL_EMULATOR" == "JetBrains-JediTerm" ]]; then
    # If PROJECT_NAME isn't set display a warning in red
    if [ -z "$PROJECT_NAME" ]; then
        echo -e "\033[0;31mWarning: PROJECT_NAME is not set - won't keep separate bash history for each project.\033[0m"
    else
        export HISTFILE=~/.bash_history_$(cleanStr "$PROJECT_NAME")
    fi
fi
