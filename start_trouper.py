#!/usr/bin/env python3

from slackbot.bot import Bot
import logging
import socket
import uuid
import os

# If you are running multiple homeops bots on the same server enable
# unique device names.
unique_device_names = False
if unique_device_names:
    os.environ['DEVICE_NAME'] = '{}-{}'.format(socket.gethostname(),
                                               uuid.uuid4())
else:
    os.environ['DEVICE_NAME'] = socket.gethostname()

# Enabling debug will reveal which Troupe device is responding to a request
os.environ['DEBUG'] = 'False'

os.environ['TARGET_DEVICE'] = 'all'
os.environ['BASE_DIR'] = os.path.join(
                             os.path.dirname(os.path.realpath(__file__)))
os.environ['ONLAUNCH'] = os.environ['BASE_DIR'] + '/.onlaunch'
os.environ['NEXTLAUNCH'] = os.environ['BASE_DIR'] + '/.nextlaunch'
os.environ['API_TOKEN'] = ''

logging.basicConfig()


def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    main()
