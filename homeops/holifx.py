from . import settings
import lifxlan
from time import sleep
import socket
import sys
import os
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)


class Lifx(object):

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
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        lifxlight = lifxlan.Light(
                        settings.plugins.lights[self.room]['macaddr'],
                        settings.plugins.lights[self.room]['ipaddr'])
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        if lifxlight.get_power() == 0:
            chat.post(":bulb: {}{} light is off.".format(debug, room_name))
        else:
            chat.post(":bulb: {}{} light is on.".format(debug, room_name))

    def toggle(self):
        try:
            settings.plugins.lights[self.room]
        except Exception:
            return
        try:
            self.isOpen(80)
        except Exception:
            return
        if not self.post.ack():
            return
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        lifxlight = lifxlan.Light(
                        settings.plugins.lights[self.room]['macaddr'],
                        settings.plugins.lights[self.room]['ipaddr'])
        if lifxlight.get_power() == 0:
            action = "on"
        else:
            action = "off"
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        chat.post(":bulb: {}Switching {} light {}."
                  .format(debug, room_name, action))
        lifxlight.set_power(action)
        self.post.unack()

    def action(self, action, timeout=None):
        action = action.lower()
        try:
            settings.plugins.lights[self.room]
        except Exception:
            return
        try:
            self.isOpen(80)
        except Exception:
            return
        if not self.post.ack():
            return
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        room_name = self.room.capitalize()
        if room_name.endswith('s'):
            room_name = room_name[:-1] + "'" + room_name[-1:]
        chat.post(":bulb: {}Switching {} light {}."
                  .format(debug, room_name, action))
        lifxlight = lifxlan.Light(
                        settings.plugins.lights[self.room]['macaddr'],
                        settings.plugins.lights[self.room]['ipaddr'])
        lifxlight.set_power(action)
        if timeout is not None:
            sleep(float(timeout)*60)
        lifxlight.set_power('off')
        self.post.unack()
