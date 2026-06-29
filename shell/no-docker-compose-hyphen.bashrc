# Prevent running the old docker-compose command by mistake.
# The new command is just docker compose.
#
# Source this from ~/.bashrc.

alias docker-compose='echo "The docker-compose command is deprecated. Use docker compose instead."'
