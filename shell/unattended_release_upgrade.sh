#!/bin/bash
# It'd be sensible to run this in tmux.
echo DPkg::options \{ \"--force-confdef\"\; \"--force-confold\"\; \} | tee /etc/apt/apt.conf.d/local
# If /etc/update-manager/release-upgrades has Prompt=never, change it to Prompt=lts.
sed -i 's/^Prompt=never/Prompt=lts/' /etc/update-manager/release-upgrades
do-release-upgrade -f DistUpgradeViewNonInteractive
# If the above command fails, look at /var/log/dist-upgrade/main.log for clues. There may be no error output,
# a suspiciously short run time may indicate a failure.
# A reboot will be required and you'll need to trigger this manually.
# 3rd party repositories may need to be configured again after the upgrade.
# Revert change to /etc/apt/apt.conf.d/local after the upgrade.
# Danger: Doing an upgrade like this is obviously risky. Have backups and a plan B!
# YMMV, but I've had successes with it:
# - from 18.04 (Bionic) to 20.04 (Focal)
# - from 20.04 (Focal) to 22.04 (Jammy)
# - from 22.04 (Jammy) to 24.04 (Noble)