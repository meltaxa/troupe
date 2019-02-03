import re
from slackbot.bot import listen_to
from . import settings
from Arlo import Arlo
from time import sleep
import os
import sys
import chatops
from slackmq import slackmq
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.arlo.bot_webhook)


def login(USERNAME, PASSWORD):
    global arlo
    arlo = Arlo(USERNAME, PASSWORD)
    global basestations
    basestations = arlo.GetDevices('basestation')


def callback(arlo, event):
    for camera in arlo.GetDevices('camera'):

        if camera['deviceId'] in event['resource']:
            cameraName = camera['deviceName']

    if eval(os.environ['DEBUG']):
        debug = "[{}] ".format(device_name)
    else:
        debug = ""
    chat.post(":footprints: {}Motion event detected from {}"
              .format(debug, cameraName))
    chat.screenplay('watchdog-{}.txt'.format(cameraName.lower()))


class MyArlo(object):
    def __init__(self):
        self.host = ""

    def set(self, string):
        self.host = string

    def who(self):
        return self.host


myArlo = MyArlo()


@listen_to('^where is watchdog', re.IGNORECASE)
def find_watchdog(message):
    if eval(os.environ['DEBUG']):
        debug = "[{}] ".format(device_name)
    else:
        debug = ""
    if myArlo.who() == device_name:
        chat.post(':dog2: {}Watchdog is running.'.format(debug))


@listen_to('^restart watchdog', re.IGNORECASE)
def restart_arlo(message):
    if myArlo.who() == device_name:
        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        onlaunch = base_dir + '/.onlaunch'
        chat.post('relaunch {}'.format(device_name))
        with open(onlaunch, 'w') as launch_file:
            print("start watchdog", file=launch_file)
    else:
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'], message.body['ts'])
        if post.ack():
            chat.post('start watchdog')
            post.unack()


@listen_to('^start watchdog', re.IGNORECASE)
def start_watchdog(message):
    if eval(os.environ['DEBUG']):
        debug = "[{}] ".format(device_name)
    else:
        debug = ""
    if myArlo.who() == device_name:
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        post.ack()
        chat.post(':warning: {}Watchdog is already running.'.format(debug))
        post.unack()
        return
    else:
        sleep(3)
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        if not post.ack():
            return
    myArlo.set(device_name)
    chat.post(':dog2: {}Watchdog started.'.format(debug))
    try:
        post.unack()
        login(settings.servers.arlo.bot_username,
              settings.servers.arlo.bot_password)
        arlo.SubscribeToMotionEvents(basestations[0], callback, timeout=120)
    except Exception:
        pass
    myArlo.set("")
    sleep(3)
    chat.post('start watchdog')
