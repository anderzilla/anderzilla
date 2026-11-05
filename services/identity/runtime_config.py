"""Translate application settings on SWA's managed Functions host.

Azure Static Web Apps reserves the IDENTITY_ prefix. Dedicated Functions use
the canonical names directly; SWA receives AZ_ACCOUNT_ aliases instead.
Only trusted process environment settings are mapped, never HTTP input.
"""
import os


def configure_settings():
    for name, value in tuple(os.environ.items()):
        if name.startswith('AZ_ACCOUNT_'):
            os.environ['IDENTITY_' + name[len('AZ_ACCOUNT_'):]] = value
