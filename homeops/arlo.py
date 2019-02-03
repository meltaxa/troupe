import re
from slackbot.bot import listen_to
from . import settings
from Arlo import Arlo
import os
import sys
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.arlo.bot_webhook)

if (settings.plugins.arlo.enabled):
    @listen_to("^arm arlo$", re.IGNORECASE)
    @listen_to("^arm$", re.IGNORECASE)
    def armarlo(message):
        """arm arlo
           Enable motion detection for the Arlo system.
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
        message.send(":rotating_light: {}Arming Arlo.".format(debug))
        arlo = Arlo(settings.servers.arlo.username,
                    settings.servers.arlo.password)
        basestations = arlo.GetDevices('basestation')
        arlo.Arm(basestations[0])
        # Perform any post arming actions via a screenplay
        chat.post("custom arlo")
        message.send(":rotating_light: {}Arlo is armed.".format(debug))
        post.unack()

    @listen_to('^disarm arlo$', re.IGNORECASE)
    @listen_to('^disarm$', re.IGNORECASE)
    def disarmarlo(message):
        """disarm arlo
           Disable motion detection for the Arlo system.
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
        message.send(":rotating_light: {}Disarming Arlo.".format(debug))
        arlo = Arlo(settings.servers.arlo.username,
                    settings.servers.arlo.password)
        basestations = arlo.GetDevices('basestation')
        arlo.Disarm(basestations[0])
        message.send(":rotating_light: {}Arlo is disarmed.".format(debug))
        post.unack()

    @listen_to('^help (arm|disarm) (arlo)', re.IGNORECASE)
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
