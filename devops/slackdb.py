import os
import sys
import chatops
from slackbot.bot import listen_to
from . import settings
from slackmq import slackmq
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.devops.bot_webhook)


@listen_to('^set (.*) (.*)')
def setslackdb(message, key, value):
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'],
                   message.body['ts'])
    os.environ[key] = value
    if post.ack():
        slack = slackmq(os.environ['OAUTH_ACCESS_TOKEN'],
                        message.body['channel'],
                        message.body['ts'])
        response = slack.pinlist()
        for pins in response.body['items']:
            if pins['message']['text'].startswith('set ' + key + ' '):
                if pins['message']['ts'] != message.body['ts']:
                    slack.unack(ts=pins['message']['ts'])


@listen_to('^purge pins')
def purgepins(message):
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'],
                   message.body['ts'])
    if post.ack():
        slack = slackmq(os.environ['OAUTH_ACCESS_TOKEN'],
                        message.body['channel'],
                        message.body['ts'])
        response = slack.pinlist()
        for pins in response.body['items']:
            if pins['message']['ts'] != message.body['ts']:
                if not pins['message']['text'].startswith('set '):
                    slack.unack(ts=pins['message']['ts'])
        post.unack()


@listen_to('^load (all|key) (.*)')
@listen_to('^load (all)')
def loadkeys(message, action, key=None):
    slack = slackmq(os.environ['OAUTH_ACCESS_TOKEN'],
                    message.body['channel'],
                    message.body['ts'])
    response = slack.pinlist()
    for pins in response.body['items']:
        pin = pins['message']['text']
        if pin.startswith('set '):
            kv = pin.split(None, 1)[1]
            pin_key = kv.split(None, 1)[0]
            pin_value = kv.split(None, 1)[1]
            if key == pin_key or action == 'all':
                os.environ[pin_key] = pin_value
                try:
                    if slack.ack():
                        message.send('Loading key {} with value {}'.format(
                                      pin_key,
                                      pin_value
                                    )
                        )
                        slack.unack()
                except Exception:
                    message.send(':warning: No such key exists')
                    return False
