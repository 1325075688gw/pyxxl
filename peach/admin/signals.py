from django import dispatch

post_add_user = dispatch.Signal()
post_del_user = dispatch.Signal()
post_update_user = dispatch.Signal()
