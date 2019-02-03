from . import settings
from pyHS100 import SmartPlug, SmartBulb
from time import sleep
import socket
import sys
import os
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)


class Tplink(object):

    def __init__(self, post, room):
        self.room = room
        self.post = post

    def isOpen(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((settings.plugins.lights[self.room]['ipaddr'],
                       int(port)))
            s.shutdown(2)
            return True
        except Exception:
            return False

    def status(self):
        try:
            settings.plugins.lights[self.room]
        except Exception:
            return
        try:
            self.isOpen(9999)
        except Exception:
            return
        type = settings.plugins.lights[self.room]['type']
        if type == 'plug':
            emoji = ':electric_plug:'
            tplinklight = SmartPlug(
                              settings.plugins.lights[self.room]['ipaddr'])
        else:
            emoji = ':bulb:'
            type = 'light'
            tplinklight = SmartBulb(
                              settings.plugins.lights[self.room]['ipaddr'])
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        if tplinklight.state == "OFF":
            chat.post("{} {}{} {} is off.".format(emoji, debug,
                      room_name, type))
        else:
            chat.post("{} {}{} {} is on.".format(emoji, debug,
                      room_name, type))

    def toggle(self):
        try:
            settings.plugins.lights[self.room]
        except Exception:
            return
        try:
            self.isOpen(9999)
        except Exception:
            return
        if not self.post.ack():
            return
        type = settings.plugins.lights[self.room]['type']
        if type == 'plug':
            emoji = ':electric_plug:'
            tplinklight = SmartPlug(
                              settings.plugins.lights[self.room]['ipaddr'])
        else:
            emoji = ':bulb:'
            type = 'light'
            tplinklight = SmartBulb(
                              settings.plugins.lights[self.room]['ipaddr'])
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        if tplinklight.state == "OFF":
            action = "ON"
        else:
            action = "OFF"
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        chat.post("{} {}Switching {} {} {}."
                  .format(emoji, debug,
                          room_name, type, action.lower()))
        tplinklight.state = action
        self.post.unack()

    def action(self, action, timeout=None):
        action = action.upper()
        try:
            settings.plugins.lights[self.room]
        except Exception:
            return
        try:
            self.isOpen(9999)
        except Exception:
            return
        if not self.post.ack():
            return
        type = settings.plugins.lights[self.room]['type']
        if type == 'plug':
            emoji = ':electric_plug:'
            tplinklight = SmartPlug(
                              settings.plugins.lights[self.room]['ipaddr'])
        else:
            type = 'light'
            emoji = ':bulb:'
            tplinklight = SmartBulb(
                              settings.plugins.lights[self.room]['ipaddr'])
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        chat.post("{} {}Switching {} {} {}.".format(emoji, debug,
                  room_name, type, action.lower()))
        tplinklight.state = action
        if timeout is not None:
            sleep(float(timeout)*60)
            tplinklight.state = 'OFF'
        self.post.unack()
