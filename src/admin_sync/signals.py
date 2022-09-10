from django import dispatch

admin_sync_data_published = dispatch.Signal()
admin_sync_data_fetched = dispatch.Signal()
admin_sync_data_received = dispatch.Signal()
