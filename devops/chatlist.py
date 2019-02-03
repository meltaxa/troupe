import os
import sys
import chatops
from slackbot.bot import listen_to
from . import settings
from slackmq import slackmq
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.devops.bot_webhook)


@listen_to('^screenplay (.*)')
def screenplay(message, filename):
    """Parse a screenplay to act out
    """
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'],
                   message.body['ts'])
    if post.ack():
        chat.screenplay(filename + '.txt')
        post.unack()
