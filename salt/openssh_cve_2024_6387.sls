# This is an ad-hoc state to upgrade OpenSSH to fix CVE-2024-6387 on Ubuntu/Debian.
# Note: Verify suitability for your environment before applying and confirm effectiveness after applying.
# Suggest targeting only os == Ubuntu or Debian
# $ salt -C 'G@os:Ubuntu or G@os:Debian' state.apply adhoc.openssh_cve_2024_6387
# References: CVE-2024-6387 https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-6387
#                           https://security-tracker.debian.org/tracker/CVE-2024-6387
#             USN-6859-1 https://ubuntu.com/security/notices/USN-6859-1
#             DSA-5724-1 https://security-tracker.debian.org/tracker/DSA-5724-1
{% set upgrade_to = {
  "Ubuntu-22.04": "1:8.9p1-3ubuntu0.10",
  "Ubuntu-23.10": "1:9.3p1-1ubuntu3.6",
  "Ubuntu-24.04": "1:9.6p1-3ubuntu13.3",
  "Debian-12": "1:9.2p1-2+deb12u3",
} %}

{% set osfinger = grains.get("osfinger") %}
{% if osfinger in upgrade_to %}
pkg.refresh_db:
  module.run:
    - pkg.refresh_db: []
{% set target_ver = upgrade_to[osfinger] %}
{% if salt["pkg.version"]("openssh-server") %}
openssh-server:
  pkg.installed:
    - version: ">={{ target_ver }}"
    - require:
      - module: pkg.refresh_db
    # Above is a workaround for refresh: True not working
{% endif %}
{% if salt["pkg.version"]("openssh-client") %}
openssh-client:
  pkg.installed:
    - version: ">={{ target_ver }}"
    - require:
      - module: pkg.refresh_db
{% endif %}
{% endif %}



