
Remove Firefox snap:
  snappkg.removed:
    - name: firefox


Make sure Firefox snap doesn't get reinstalled:
  file.managed:
    - name: /etc/apt/preferences.d/firefox-no-snap
    - contents: |
        Package: firefox*
        Pin: release o=Ubuntu*
        Pin-Priority: -1
    - user: root
    - group: root
    - mode: 644


Mozilla PPA:
  pkgrepo.managed:
    - ppa: 'mozillateam/ppa'


Prefer Mozilla PPA:
  file.managed:
    - name: /etc/apt/preferences.d/mozilla-firefox
    - contents: |
        Package: *
        Pin: release o=LP-PPA-mozillateam
        Pin-Priority: 1001
    - user: root
    - group: root
    - mode: 644


Install Firefox:
  pkg.installed:
    - name: firefox
    - fromrepo: ppa:mozillateam/ppa
    - require:
      - pkgrepo: Mozilla PPA
      - file: Prefer Mozilla PPA
      - snappkg: Remove Firefox snap
