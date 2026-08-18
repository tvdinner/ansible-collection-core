# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Joe Stump <joe@joestump.net>
# MIT License (see LICENSE)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.tvdinner.core.plugins.module_utils.client import (  # noqa: F401
    AUTH_BEARER,
    AUTH_HEADER,
    AUTH_NONE,
    AUTH_TOKEN,
    RESTClient,
    TVDinnerError,
    TVDinnerNotFoundError,
)


def connection_argument_spec(url_key, token_key):
    """Return the connection argument spec shared by every module.

    Each collection names its own parameters (C(gitea_url>/C(gitea_token),
    C(api_url>/C(api_key), ...) so playbooks read naturally; the shape and
    defaults stay identical everywhere.
    """
    return dict(
        **{
            url_key: dict(type='str', required=True),
            token_key: dict(type='str', required=True, no_log=True),
        },
        validate_certs=dict(type='bool', default=True),
        timeout=dict(type='int', default=30),
    )


def client_from_module(module, client_class, url_key, token_key, **kwargs):
    """Build a RESTClient subclass from module parameters.

    Args:
        module: AnsibleModule instance.
        client_class: RESTClient subclass to instantiate.
        url_key: module parameter holding the base URL.
        token_key: module parameter holding the API token.
        kwargs: extra constructor arguments (e.g. auth_style).
    """
    return client_class(
        url=module.params[url_key],
        token=module.params[token_key],
        validate_certs=module.params['validate_certs'],
        timeout=module.params['timeout'],
        **kwargs
    )


def normalize_list(value):
    """Normalize a list for idempotency comparison: sorted, deduplicated."""
    if value is None:
        return []
    return sorted(set(value))


def normalize_dict_subset(source, keys):
    """Project C(keys) out of C(source), dropping None values.

    Used to compare only the fields a module manages, ignoring
    server-populated metadata (timestamps, ids) that would make every run
    report changed.
    """
    if source is None:
        return {}
    return {k: source[k] for k in keys if source.get(k) is not None}


def calculate_diff(before, after, module):
    """Return an ansible exit diff honoring check mode.

    Args:
        before: current state (dict, or None when absent).
        after: desired state (dict, or None when deleting).
        module: AnsibleModule instance (used for check mode).

    Returns:
        Dict with C(changed), C(diff), and the before/after values.
    """
    changed = (before or {}) != (after or {})
    result = dict(
        changed=changed,
        before=before,
        after=after,
    )
    if module._diff:
        result['diff'] = dict(
            before=before,
            after=after,
        )
    return result
