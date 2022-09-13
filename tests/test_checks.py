from admin_sync.checks import check_admin_sync_settings


def test_check_admin_sync_settings(settings):
    """Ok if 'reversion' in INSTALLED_APPS"""
    settings.ADMIN_SYNC_USE_REVERSION = True
    assert check_admin_sync_settings(None) == []


def test_check_admin_sync_settings_ok(settings, monkeypatch):
    """Ok if ADMIN_SYNC_USE_REVERSION == False"""
    settings.ADMIN_SYNC_USE_REVERSION = False
    assert check_admin_sync_settings(None) == []


def test_check_admin_sync_settings_error(settings, monkeypatch):
    """Error if 'reversion' is not available"""
    settings.ADMIN_SYNC_USE_REVERSION = True
    monkeypatch.setattr("django.apps.apps.is_installed", lambda s: False)
    assert check_admin_sync_settings(None)
