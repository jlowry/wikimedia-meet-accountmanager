#
# Regular cron jobs for the meet-accountmanager package
#
0 4	* * *	root	[ -x /usr/bin/meet-accountmanager_maintenance ] && /usr/bin/meet-accountmanager_maintenance
