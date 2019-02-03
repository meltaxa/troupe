from slackbot.bot import listen_to
from . import settings
import re
import os
import sys
from slackmq import slackmq
from time import sleep
import chatops

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

base_dir = os.environ['BASE_DIR']
device_name = os.environ['DEVICE_NAME']

chat = chatops.Chatops(settings.servers.devops.bot_webhook)


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)


@listen_to('^roll (.*)', re.IGNORECASE)
def roll(message, command):
    if 'call' == command:
        return
    thread_ts = message.body['ts']
    last_roll = base_dir + '/.cache/.last_roll'
    touch(last_roll)
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'], thread_ts)
    if not post.ack():
        return
    sleep(1)
    message.reply('[{}] Rolling: {}'
                  .format(device_name, command), in_thread=True)
    chat.post('target {}'.format(device_name), thread_ts)
    chat.post(command, thread_ts)
    chat.post('target all', thread_ts)
    with open(last_roll, 'w') as last_file:
        print('{}\n{}'.format(thread_ts, command), file=last_file)
    post.unack()
    chat.post('rolling {} {}'.format(thread_ts, command), thread_ts)


@listen_to(r'^rolling (\d+\.\d+) (.*)', re.IGNORECASE)
def rolling(message, thread_ts, command):
    last_roll = base_dir + '/.cache/.last_roll'
    touch(last_roll)
    if thread_ts not in open(last_roll).read():
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'], thread_ts)
        if not post.ack():
            return
        with open(last_roll, 'w') as last_file:
            print('{}\n{}'.format(thread_ts, command), file=last_file)
        post.unack()
        chat.post('[{}] Rolling:'.format(device_name), thread_ts)
        chat.post('target {}'.format(device_name), thread_ts)
        chat.post(command,  thread_ts)
        chat.post('target all', thread_ts)
        chat.post('rolling {} {}'.format(thread_ts, command), thread_ts)


@listen_to('^!(.*)', re.IGNORECASE)
def run(message, command):
    if (os.environ['TARGET_DEVICE'] != 'all' and
       os.environ['TARGET_DEVICE'] != device_name):
        return
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'], message.body['ts'])
    if not post.ack():
        return
    message.send(os.popen(command).read())
    post.unack()
