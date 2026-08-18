# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Joe Stump <joe@joestump.net>
# MIT License (see LICENSE)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
name: connection
short_description: Shared TLS and timeout options
description:
  - The connection options every tvdinner.* module repeats. Service URL and
    token options differ per collection (C(gitea_url), C(lldap_url), ...) and
    are documented by each module; TLS verification and timeout are identical
    everywhere and live here.
options:
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
  timeout:
    description:
      - Request timeout in seconds.
    type: int
    default: 30
'''
