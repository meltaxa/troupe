from slackbot.bot import listen_to
import re
from slacker import Slacker
import local_settings
import os
import sys
import shutil
from time import sleep
import requests
from threading import Thread
from slackmq import slackmq
import json
import chatops

version = open(os.path.join(
               os.path.dirname(__file__), 'VERSION')).read().strip()

base_dir = os.environ['BASE_DIR']
onlaunch = os.environ['ONLAUNCH']
nextlaunch = os.environ['NEXTLAUNCH']
device_name = os.environ['DEVICE_NAME']
os.environ['CHANNEL_NAME'] = local_settings.CHANNEL_NAME
os.environ['API_TOKEN'] = local_settings.API_TOKEN
os.environ['OAUTH_ACCESS_TOKEN'] = local_settings.OAUTH_ACCESS_TOKEN
if eval(os.environ['DEBUG']):
    debug = "[{}] ".format(device_name)
else:
    debug = ""

try:
    os.makedirs(base_dir + '/.cache')
except Exception:
    pass

# Seconds to wait for avoiding the Slack rate_limit
rate_limit = 3


def launch():
    tmp_launch = base_dir + '/.tmplaunch'
    # Concat onlaunch and nextlaunch files
    with open(tmp_launch, 'wb') as wfd:
        for f in [onlaunch, nextlaunch]:
            if os.path.isfile(f):
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024*1024*10)

    if os.path.isfile(tmp_launch):
        with requests.sessions.Session() as session:
            slack = Slacker(local_settings.API_TOKEN, session=session)
            slack.chat.post_message(
                local_settings.CHANNEL_NAME, ':performing_arts: [' +
                device_name + '] Troupe ' + version +
                ' started.')
            while True:
                if 'devops' in sys.modules:
                    sleep(rate_limit)
                    break
                else:
                    sleep(1)
            with open(tmp_launch, 'r') as launch_file:
                for line in launch_file:
                    line = line.format(device_name=device_name)
                    if line[0] != '#':
                        slack.chat.post_message(local_settings.CHANNEL_NAME,
                                                line)
                        sleep(rate_limit)
            os.remove(tmp_launch)
    if os.path.isfile(nextlaunch):
        os.remove(nextlaunch)


t1 = Thread(target=launch)
t1.start()


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd
                 else fname, dir_fd=None if os.supports_fd
                 else dir_fd, **kwargs)


@listen_to('^roll call', re.IGNORECASE)
def roll_call(message):
    """Ask all Troupe bots to report in.
    """
    sleep(rate_limit)
    message.send(device_name + ' is here, at version ' + version)


@listen_to('^debug$', re.IGNORECASE)
@listen_to('^debug (.*)', re.IGNORECASE)
def setupDebug(message, action='toggle'):
    """Reveal which Troupe bot device is handling requests.
    """
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'], message.body['ts'])
    action = action.lower()
    if action == 'toggle':
        if eval(os.environ['DEBUG']):
            os.environ['DEBUG'] = 'False'
            if not post.ack():
                return
            message.send(':gear: Debug is disabled')
            post.unack()
        else:
            os.environ['DEBUG'] = 'True'
            if not post.ack():
                return
            message.send(':gear: [{}] Debug is enabled.'
                         .format(os.environ['DEVICE_NAME']))
            post.unack()
        return
    else:
        if action in ['on', 'enabled', 'true']:
            action = True
            debug = "[{}] ".format(os.environ['DEVICE_NAME'])
        else:
            action = False
            debug = ""
        os.environ['DEBUG'] = str(action)
        if not post.ack():
            return
        message.send(':gear: {}Debug is {}.'
                     .format(debug, ['disabled', 'enabled'][action]))
        post.unack()


@listen_to('^bot count$', re.IGNORECASE)
def count(message):
    """Report on the current connections count.
       Slack has a limit on the number of concurrent Bot connections. Max: 17
       Reference: https://github.com/slackapi/node-slack-sdk/issues/166
    """
    if (os.environ['TARGET_DEVICE'] != 'all' and
       os.environ['TARGET_DEVICE'] != device_name):
        return
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'], message.body['ts'])
    if post.ack():
        check = chatops.Chatops('https://slack.com/api/users.getPresence')
        result = json.loads(check.getpresence())
        connection_count = result['connection_count']
        message.send('{}I have {} connections to Slack.'
                     .format(debug, connection_count))
        post.unack()
