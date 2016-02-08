#!/usr/bin/env python

import os
import sys
from functools32 import lru_cache
from collections import defaultdict
import yaml
import dbus
from dbus.mainloop.qt import DBusQtMainLoop
from PyQt4 import QtGui, QtCore
import re
import signal

PURPLE_MESSAGE_DELAYED = 0x400

purple = None
config = {}
tray_icon = None
message_log = []
MAX_LOG_LINES = 8
MAX_LOG_LINE_LENGTH = 250

class DotDict(defaultdict):
    """Allows attribute-like access.  Returns {} when an item is accessed that
    is not in the dict."""

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(dict, *args, **kwargs)


    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            return self.__missing__(attr)


# The following magic makes yaml use DotDict instead of dict
def dotdict_constructor(loader, node):
    return DotDict(loader.construct_pairs(node))


yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dotdict_constructor)


def read_config(path):
    global config

    with open(path) as config_file:
        config = yaml.load(config_file)

    config.notify.ping = re.compile(config.notify.ping, re.I)
    config.notify.at_here = re.compile(config.notify.at_here, re.I)

    #print config


def shell_escape(string):
    return string.replace("'", "'\\''")


def play(sound):
    os.system("/usr/bin/paplay %s '%s'" % (config.notify.get('paplay_args', ''), shell_escape(sound)))


def notify(subject, message):
#    subject = shell_escape(subject)
#    message = shell_escape(message)
#    command = "/usr/bin/notify-send '%s' '%s'" % (subject, message)
#    os.system(command)
    tray_icon.showMessage(subject, message)

def truncate(string, length):
    if len(string) > length:
        return string[:length - 3] + "..."
    else:
        return string

def log(message):
    global message_log

    message_log.append(truncate(message, MAX_LOG_LINE_LENGTH))
    message_log = message_log[-MAX_LOG_LINES:]
    
    menu = tray_icon.contextMenu()
    menu.clear()

    for line in message_log:
        menu.addAction(line)

    print message

def ping(message):
    log("PING: " + message)
    play(config.sounds.ping)
    notify("HipChat Ping", message)


def pm(message):
    log("PM:" + message)
    play(config.sounds.pm)
    notify("HipChat PM", message)


def chat_message_received(account, sender, message, conversation_id, flags):
    print >> sys.stderr, sender, "said:", message
    #print >> sys.stderr, account
    #print >> sys.stderr, chat
    print >> sys.stderr, flags
    #print >> sys.stderr

    if flags & PURPLE_MESSAGE_DELAYED:
        return

    chat = get_conversation_title(conversation_id)

    if sender != config.notify.my_name:
        if config.notify.ping.search(message) or \
                (config.notify.at_here.search(message) and
                 chat in config.notify.at_here_chats):
            ping("[%s] %s: %s" % (chat, sender, message))


def im_message_received(account, sender_id, message, conversation, flags):
    print >> sys.stderr, sender_id, "IM:", message
    #print >> sys.stderr, account
    #print >> sys.stderr, conversation
    print >> sys.stderr, flags
    #print >> sys.stderr

    if flags & PURPLE_MESSAGE_DELAYED:
        return

    sender = get_im_sender_name(account, sender_id)

    pm("%s: %s" % (sender, message))


@lru_cache()
def get_im_sender_name(account, sender_id):
    return purple.PurpleBuddyGetAlias(purple.PurpleFindBuddy(account, sender_id))

@lru_cache()
def get_conversation_title(id):
    return purple.PurpleConversationGetTitle(id)


def main():
    if len(sys.argv) != 2:
        return "usage: %s <config file>" % sys.argv[0]

    read_config(sys.argv[1])

    global purple, tray_icon

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtGui.QApplication(sys.argv)

    DBusQtMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
    purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

    bus.add_signal_receiver(chat_message_received,
                            dbus_interface="im.pidgin.purple.PurpleInterface",
                            signal_name="ReceivedChatMsg")

    bus.add_signal_receiver(im_message_received,
                            dbus_interface="im.pidgin.purple.PurpleInterface",
                            signal_name="ReceivedImMsg")

    tray_icon = QtGui.QSystemTrayIcon()
    tray_icon.setIcon(QtGui.QIcon('/home/lex/icons/hipchat.png'))
    menu = QtGui.QMenu()
    tray_icon.setContextMenu(menu)
    tray_icon.show()
    #tray_icon.showMessage("foo", "bar")

    print "starting"
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
