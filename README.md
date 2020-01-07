Synology API modules
=========

Modules that poke Synology APIs via `synowebapi` executable, as well as a
helper library for implementing your own modules.

Example Playbook
----------------

```yaml
---
- hosts: all
  roles:
    - role: gelraen.synowebapi
  tasks:
    - name: Add reverse proxy entries
      become: yes
      syno_reverse_proxy:
        name: 'DSM'
        backend:
          fqdn: localhost
          port: 5000
        frontend:
          fqdn: 'dsm.lan'
```

License
-------

MIT
