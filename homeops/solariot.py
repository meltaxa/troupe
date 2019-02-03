import re
import requests
from slackbot.bot import listen_to
from slacker import Slacker
from . import settings
import sys
import os
from slackmq import slackmq
import local_settings
import chatops
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.homeops.bot_webhook)

if (settings.plugins.solariot.enabled):
    slack = Slacker(local_settings.API_TOKEN)

    def download_image(url, fpath):
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        r = requests.get(url, stream=True)
        with open(fpath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*64):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                f.flush()
        return fpath

    @listen_to('^solar (.*)$', re.IGNORECASE)
    def solar(message, graph):
        """solar <graph name>
           Display a SolarIot Grafana panel
        """
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        graph = graph.lower()
        try:
            graph_url = settings.plugins.solariot[graph]['url']
        except Exception:
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
        filename = os.environ['BASE_DIR'] + '/.cache/solargraph.png'
        download_image(graph_url, filename)
        slack.files.upload(
            filename, channels=[local_settings.CHANNEL_NAME],
            title=settings.plugins.solariot[graph]['title'],
            initial_comment=debug
        )
        os.remove(filename)
        post.unack()

    @listen_to('^help (solar)', re.IGNORECASE)
    def help(message, command):
        if (os.environ['TARGET_DEVICE'] != 'all' and
           os.environ['TARGET_DEVICE'] != device_name):
            return
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'], message.body['ts'])
        try:
            desc = eval(command).__doc__
        except Exception:
            return
        if not post.ack():
            return
        chat.help(desc)
        post.unack()
