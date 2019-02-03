import re
from slackbot.bot import listen_to
from . import settings
from . import holifx
from . import hotplink
import sys
import os
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)

#
# Master Light Switch to manage various bulb and plug vendors
# such as Tp-Link and Lifx.
#

if (settings.plugins.lights.enabled):
    @listen_to('^switch (.*) (on|off)$', re.IGNORECASE)
    @listen_to('^switch (.*) light (on|off)$', re.IGNORECASE)
    @listen_to('^switch (.*) (on|off) for (.*) minutes$', re.IGNORECASE)
    @listen_to('^switch (.*) light (on|off) for (.*) minutes$', re.IGNORECASE)
    def switch(message, light, action, timeout=None):
        """switch <light name> [light] (on|off) [for <number> minutes]
           Manage smart bulbs and plugs with an optional timer.
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        light = light.lower()
        action = action.lower()
        try:
            vendor = settings.plugins.lights[light]['vendor']
        except Exception:
            return
        if vendor == 'lifx':
            bulb = holifx.Lifx(slackmq(os.environ['API_TOKEN'],
                                       message.body['channel'],
                                       message.body['ts']),
                               light)
            bulb.action(action, timeout)
        elif vendor == 'tplink':
            bulb = hotplink.Tplink(slackmq(os.environ['API_TOKEN'],
                                           message.body['channel'],
                                           message.body['ts']),
                                   light)
            bulb.action(action, timeout)

    @listen_to('^toggle (.*) light$', re.IGNORECASE)
    def toggle_light(message, light, timeout=None):
        """toggle <light name> light
           Switch light on or off
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        light = light.lower()
        try:
            vendor = settings.plugins.lights[light]['vendor']
        except Exception:
            return
        if vendor == 'lifx':
            bulb = holifx.Lifx(slackmq(os.environ['API_TOKEN'],
                                       message.body['channel'],
                                       message.body['ts']),
                               light)
            bulb.toggle()
        elif vendor == 'tplink':
            bulb = hotplink.Tplink(slackmq(os.environ['API_TOKEN'],
                                           message.body['channel'],
                                           message.body['ts']),
                                   light)
            bulb.toggle()

    @listen_to('^lights$', re.IGNORECASE)
    def lights(message):
        """lights
           Show which lights or plugs are on or off.
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        if not post.ack():
            return
        for k, v in settings.plugins.lights.items():
            try:
                vendor = v['vendor']
            except Exception:
                continue
            if vendor == 'lifx':
                bulb = holifx.Lifx(slackmq(os.environ['API_TOKEN'],
                                           message.body['channel'],
                                           message.body['ts']),
                                   k)
                bulb.status()
            elif vendor == 'tplink':
                bulb = hotplink.Tplink(slackmq(os.environ['API_TOKEN'],
                                               message.body['channel'],
                                               message.body['ts']),
                                       k)
                bulb.status()
        post.unack()

    @listen_to('^help (switch)', re.IGNORECASE)
    @listen_to('^help (lights)', re.IGNORECASE)
    def help(message, command):
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        try:
            desc = eval(command).__doc__
        except Exception:
            return
        if not post.ack():
            return
        chat.help(desc)
        post.unack()
