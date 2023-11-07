Let's say we want to meet every directory that matches this pattern /var/tmp/whatever-*/ (e.g. /var/tmp/whatever-1/, /var/tmp/whatever-2/, etc.) and remove them. We can do this with Salt like so:

As a standalone command:

    $ salt-call file.find "/var/tmp/whatever-*/" maxdepth=0 delete=d

This is run on the minion itself, but the same could be run on the master with `salt TARGET file.find "/var/tmp/whatever-*/" maxdepth=0 delete=d` to run it on a minion named TARGET.

The quotes are important to prevent the shell from expanding the glob. The `maxdepth` parameter is used to prevent the find command from recursing into subdirectories. The `delete` parameter is used to delete the directories. The `d` is used to tell find to only delete directories. If we wanted to delete files, we could use `f` instead.

We can use module.run if we want to incorporate this into a state file:

```yaml
Remove all whatever prefixed directories (new style module.run):
    module.run:
        - file.find:
            - path: /var/tmp/whatever-*/
            - maxdepth: "0"
            - delete: d
              
Remove all whatever prefixed directories (old style module.run):
    module.run:
        - name: file.find
        - path: /var/tmp/whatever-*/
        - maxdepth: "0"
        - delete: d
```

Further reading:
- [Salt module.run docs](https://docs.saltproject.io/en/latest/ref/states/all/salt.states.module.html)
- [Salt file.find docs](https://docs.saltproject.io/en/latest/ref/modules/all/salt.modules.file.html#salt.modules.file.find)