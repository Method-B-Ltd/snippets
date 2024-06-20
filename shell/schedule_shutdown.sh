#!/bin/bash
# Shows how to schedule a shutdown at a specific time with systemd-run and systemctl.
# This example will schedule a shutdown at 10:00 on Saturday 22nd June 2024.
systemd-run --unit=scheduled_shutdown --on-calendar="2024-06-22 10:00:00" /usr/bin/systemctl poweroff
# The above works for Jammy, for Focal the command is /bin/systemctl poweroff
# To cancel the scheduled shutdown, run:
#   systemctl stop scheduled_shutdown.timer
# The timer will appear on this list:
#   systemctl list-timers
# Note that from systemd version 254 onwards, you can use systemctl poweroff --when="2024-06-22 10:00:00".
# This approach with systemd-run was used on Ubuntu 22.04 (Jammy) which has systemd version 249.
# The systemd-run command is very useful for adhoc scheduling of tasks on a Linux system.