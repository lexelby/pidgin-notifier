Pidgin Notifier
===============

HipChat's notifications for Linux suck.  You can't configure the sound and the popups don't integrate well.  Much like with [slack-tray](https://github.com/lexelby/slack-tray/), I wrote this script to replace HipChat's notifications and make them not suck for my use case.

HipChat's API isn't anywhere near as nice as Slack's.  Instead, I keep Pidgin connected via XMPP and running minimized, and pidgin-notifier uses its DBUS API to react to messages.
