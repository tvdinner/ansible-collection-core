# tvdinner.core

Shared foundation for the [tvdinner](https://gitea.stump.rocks/tvdinner)
collection family — reusable Ansible for self-hosting.

## What's in it

- **`tvdinner.core.service` role** — manage a self-hosted Docker service on a
  StumpCloud node: container, networks, caddy vhost, backups wiring.
- **`tvdinner.core.node` role** — node baseline: docker, users, storage, swap,
  caddy, edge hardening, self-healing.
- **`plugins/module_utils`** — the shared `RESTClient` and helpers every
  `tvdinner.*` API collection builds on. One client instead of seven bespoke
  copies: URL joining, query params, JSON handling, timeout, TLS verification,
  token/bearer/basic/header auth, structured errors, and a check-mode-safe
  diff helper.

## Using the client in another collection

```python
from ansible_collections.tvdinner.core.plugins.module_utils.client import (
    AUTH_TOKEN, RESTClient)
from ansible_collections.tvdinner.core.plugins.module_utils.common import (
    client_from_module, connection_argument_spec)

class GiteaClient(RESTClient):
    def __init__(self, url, token, **kwargs):
        super(GiteaClient, self).__init__(url, token, auth_style=AUTH_TOKEN, **kwargs)

    def get_user(self, username):
        return self.request('GET', '/api/v1/users/{0}'.format(username))
```

Modules get their connection options from
`connection_argument_spec('gitea_url', 'gitea_token')` and build the client
with `client_from_module(module, GiteaClient, 'gitea_url', 'gitea_token')`.

## Install

```sh
ansible-galaxy collection install git+https://gitea.stump.rocks/tvdinner/ansible-collection-core.git
```

## Development

```sh
make check   # lint + test
```

## License

MIT
