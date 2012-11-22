# script to automatically create bookmarks folder in member's user area
context.plone_log("Post create script running")
context.restrictedTraverse('@@libertic_post_create')()

