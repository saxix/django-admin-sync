from unittest.mock import Mock

from admin_sync.smart_panel import panel_admin_sync


def test_panel_admin_sync(rf):
    request = rf.get("/")
    response = panel_admin_sync(Mock(each_context=lambda a: {}), request)
