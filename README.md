# Troupe

Troupe is a distributed program of Slack bots working together to monitor and control your smart home.

Troupe was [built out of necessity][1]. It has a minimal technology stack: somewhere to run the Troupe Python script and a connection to Slack and the IoT devices. Install Troupe on another computer, and out of the box it is highly available with no extra service or configuration required. Integrate this GitHub repository to Slack and you'll get Continuous Delivery, Canary Deployments and Rolling Updates to the federation of Slack bot devices, all with zero downtime.

It is a work in progress and I welcome contributions for enhancements and additional smart home device integration. 

## Supported Smart Home Devices

This is list of my IoT devices:

* Arlo Pro security camera.
* Chromecast Audio.
* LIFX smart bulbs.
* LinkTap.
* TP-Link smart bulbs and plugs.
* WirelessTag sensors.

Troupe is extensible. If the IoT device has an API, endpoint or a ready made Python library, it can be integrated.

## Pre-requisites
* Slack workspace. 
  * Create a #homeops and #botlogs channel.
* Python 3
* GitHub or GitLab integration*. 
  * Clone this repo.
  * Create another repo, troupe-properties just for settings and other customizations.

*Optional: Enable GitHub / Travis CI or GitLab integration for DevOps features such as Continuous Delivery, Canary Deployments and Rolling Updates.

## Installation
```bash
> git clone https://github.com/meltaxa/troupe.git
> cd troupe
> pip3 install -r requirements.txt
```

## Configuration

### Generate Slack bot API token
* Go to https://api.slack.com/bot-users and create a new bot. Call it HomeOps Bot.
* Permissions → Scopes: Send messages as HomeOps chat:write:bot
* Install App to Workspace

#### Get the Slack bot OAUTH token
From https://api.slack.com/apps → OAuth & Permissions

### Create a Slack Incoming Webhook
Go to https://api.slack.com/incoming-webhooks and create an incoming-webhook. Call it HomeOps Bot.
Copy `local_settings-sample.py` to `local_settings.py` and fill the bot token details.

### Configure Troupe
Copy `homeops/settings-sample.yml` to `homeops/settings.yml` and activate/configure each plugin according to your needs.
Repeat for the devops/settings.yml file.

## Launch
```
> cd path/to/trouper
> ./start_trouper.py
```

## Recommended Integrations

* Add the GitHub Slack app to your workspace.
  * In the #homeops channel: ```/github subscribe meltaxa/troupe commits:all```
  * Do the same for your custom troupe-properties repo.
* Add the Travis CI app to your Slack workspace.
  * If you want a robust Continuous Delivery workflow, unsubscribe the GitHub meltaxa/troupe repo from Slack and...
  * Only allow successful Travis builds to trigger a Continuous Delivery workflow. You'll need to clone the GitHub Troupe repo.
  * Replace the Travis token in the devops/settings.yml file with your encrypted token.
  * Keep the GitHub troupe-properties repo subscribed to your Slack workspace. Any changes to settings will still trigger the Continuous Delivery workflow. 

## Tips

* Use static IP addresses for WiFi enabled IoT devices.
* Troupe can be called by Slack indirectly using incoming-webhooks. For example, use a hacked Amazon Dash button to make a Slack webhook URL call to perform an action.

[1]: https://medium.com/@mellican/the-travelling-homeops-troupe-c47e80dd48d9
