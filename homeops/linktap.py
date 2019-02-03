import re
import requests
from slackbot.bot import listen_to
from . import settings
import os
import sys
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)

if (settings.plugins.linktap.enabled):

    @listen_to('^tap (on|off)$', re.IGNORECASE)
    @listen_to('^tap (on) for (.*) minutes', re.IGNORECASE)
    @listen_to('^sprinkler (on|off)$', re.IGNORECASE)
    @listen_to('^sprinkler (on) for (.*) minutes', re.IGNORECASE)
    def tap(message, action, duration=5):
        """tap <on|off> [for <number> minutes]
           Turn a water tap on or off with optional timer.
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        if not post.ack():
            return
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        if action == "off":
            duration = 0
            tap_message = ":potable_water: {} \
                          Turning the sprinkler off".format(debug)
        else:
            tap_message = ":potable_water: {}Turning the sprinkler on \
                          for {} minutes".format(debug, duration)
        payload = {
            'username': settings.servers.linktap.username,
            'apiKey': settings.servers.linktap.apikey,
            'gatewayId': settings.servers.linktap.gatewayid,
            'taplinkerId': settings.servers.linktap.taplinkerid,
            'action': 'true',
            'duration': duration,
            'eco': 'false'
        }
        message.send(tap_message)
        requests.post(
            settings.servers.linktap.host + 'activateInstantMode',
            data=payload
        )
        post.unack()

    @listen_to('^help (tap)', re.IGNORECASE)
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
