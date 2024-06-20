#!/bin/bash
# It'd be sensible to run this in tmux.
echo DPkg::options \{ \"--force-confdef\"\; \"--force-confold\"\; \} | tee /etc/apt/apt.conf.d/local
do-release-upgrade -f DistUpgradeViewNonInteractive
# If the above command fails, look at /var/log/dist-upgrade/main.log for clues. There may be no error output,
# a suspiciously short run time may indicate a failure.
# A reboot will be required and you'll need to trigger this manually.
# 3rd party repositories may need to be configured again after the upgrade.
# Revert change to /etc/apt/apt.conf.d/local after the upgrade.
# Danger: Doing an upgrade like this is obviously risky, but I've had successes with it
# from 18.04 (Bionic) to 20.04 (Focal) and from 20.04 (Focal) to 22.04 (Jammy). Have backups and a plan B!