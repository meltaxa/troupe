import re
from slackbot.bot import listen_to
from . import settings
import wirelesstagpy
import os
import sys
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)

if (settings.plugins.wirelesstags.enabled):
    @listen_to("^show sensors", re.IGNORECASE)
    def showsensors(message):
        """show sensors
           Display WirelessTags sensor readings for all tags.
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'], message.body['ts'])
        if not post.ack():
            return
        username = settings.servers.wirelesstags.username
        password = settings.servers.wirelesstags.password
        api = wirelesstagpy.WirelessTags(username=username,
                                         password=password)
        sensors = api.load_tags()
        for (uuid, tag) in sensors.items():
            message.send(
              'Loaded sensor: {0}, \
               temp: {1}, \
               humidity: {2} \
               probe taken: {3}'.format(
               tag.name, tag.temperature,
               tag.humidity, tag.time_since_last_update))
        post.unack()

    @listen_to('^help (show) (.*)$', re.IGNORECASE)
    def help(message, command, args):
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'], message.body['ts'])
        try:
            command = command + args.replace(' ', '_')
            desc = eval(command).__doc__
        except Exception:
            return
        if not post.ack():
            return
        chat.help(desc)
        post.unack()
