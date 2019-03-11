import re
from slackbot.bot import listen_to
from . import settings
import pychromecast
import os
import sys
from slackmq import slackmq
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)


if (settings.plugins.chromecastaudio.enabled):
    chromecasts = pychromecast.get_chromecasts()

    @listen_to('^play (.*) on (.*)', re.IGNORECASE)
    @listen_to(r'^play (\w+)$', re.IGNORECASE)
    def play(message, sound_effect, speaker_name='default'):
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
        if speaker_name == 'default':
            speaker_name = settings.plugins.chromecastaudio.default
        cast = next(cc for cc in chromecasts
                    if cc.device.friendly_name == speaker_name)
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

    @listen_to('^volume (.*) on (.*)', re.IGNORECASE)
    @listen_to(r'^volume (\w+)$', re.IGNORECASE)
    def volume(message, level, speaker_name='default'):
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
        if speaker_name == 'default':
            speaker_name = settings.plugins.chromecastaudio.default
        if eval(os.environ['DEBUG']):
            debug = "[{}] ".format(device_name)
        else:
            debug = ""
        message.send(":loud_sound: {}Setting the speaker volume to {}%."
                     .format(debug, level))
        cast = next(cc for cc in chromecasts
                    if cc.device.friendly_name == speaker_name)
        cast.wait()
        cast.set_volume(float(level)/100)
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
