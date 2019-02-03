import re
from slackbot.bot import listen_to
from . import settings
import pychromecast
import socket
import os
import sys
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)


def isOpen(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, int(port)))
        return True
    except Exception:
        return False
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()


if (settings.plugins.chromecastaudio.enabled) and \
   isOpen(settings.plugins.chromecastaudio.ipaddress, 8008):
    cast = pychromecast.Chromecast(settings.plugins.chromecastaudio.ipaddress)

    @listen_to('^play (.*)', re.IGNORECASE)
    def play(message, sound_effect):
        """play <audio url or alias>
           Stream an audio file from a given URL (or alias).
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
        if 'http' in sound_effect:
            sound = sound_effect.replace('<', '')
            sound = sound.replace('>', '')
        else:
            sound = settings.plugins.chromecastaudio.media[sound_effect]
        message.send(":loud_sound: {}Playing {} on the speaker."
                     .format(debug, sound_effect))
        mc = cast.media_controller
        cast.wait()
        mc.play_media(sound, 'audio/mp3')
        mc.block_until_active()
        post.unack()

    @listen_to('^volume (.*)', re.IGNORECASE)
    def volume(message, this):
        """volume <percent level>
           Set the volume level (percent).
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
        message.send(":loud_sound: {}Setting the speaker volume to {}%."
                     .format(debug, this))
        cast.set_volume(float(this)/100)
        post.unack()

    @listen_to('^help (play|volume)', re.IGNORECASE)
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
