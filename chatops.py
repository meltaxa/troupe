from time import sleep
import requests
import os


class Chatops(object):

    def __init__(self, webhook):
        self.webhook = webhook

    def help(self, message):
        lines = message.splitlines()
        payload = {
            "color": "#439FE0",
            "title": lines[0],
            "text": lines[1].lstrip(),
            "mrkdwn": True
        }
        response = requests.post(
            self.webhook, json={"attachments": [payload]},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
        sleep(1)

    def getpresence(self):
        response = requests.get(
                 self.webhook,
                 headers={'Content-Type': 'application/x-www-form-urlencoded'},
                 params={'token': os.environ['API_TOKEN']}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
        else:
            sleep(1)
            return response.text

    def post(self, message, thread_ts=None):
        response = requests.post(
            self.webhook, json={"text": message,
                                "thread_ts": thread_ts},
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
        sleep(1)

    def screenplay(self, filename):
        filename = 'screenplays/' + filename
        if os.path.isfile(filename):
            with open(filename, 'r') as chat_file:
                for command in chat_file:
                    if command[0] == '>':
                        eval(command[1:].strip())
                    elif command[0] != '#':
                        self.post(command)

    def history(self, token, channel, timestamp):
        payload = {'token': token,
                   'channel': channel,
                   'latest': timestamp,
                   'inclusive': True,
                   'count': 1}
        response = requests.get(
            'https://slack.com/api/channels.history', params=payload
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
        else:
            return response
