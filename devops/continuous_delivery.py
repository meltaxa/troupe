import chatops
import fnmatch
import glob
import os
import re
import requests
from slackbot.bot import listen_to, on_reaction
from slackbot.utils import download_file
from slacker import Slacker
from slackmq import slackmq
import shutil
import sys
import tarfile
from time import sleep, localtime, time
import zipfile
from . import settings
import pip
from pip.req import parse_requirements
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

base_dir = os.environ['BASE_DIR']
onlaunch = os.environ['ONLAUNCH']
nextlaunch = os.environ['NEXTLAUNCH']
device_name = os.environ['DEVICE_NAME']
chat = chatops.Chatops(settings.servers.devops.bot_webhook)
topic = chatops.Chatops('https://slack.com/api/channels.history')
if eval(os.environ['DEBUG']):
    debug = "[{}] ".format(device_name)
else:
    debug = ""

# Seconds to wait for avoiding the Slack rate_limit
rate_limit = 3


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd
                 else fname, dir_fd=None if os.supports_fd
                 else dir_fd, **kwargs)


def download_artifact(url, fpath, token=''):
    if token:
        if 'gitlab' in url:
            headers = {"PRIVATE-TOKEN": token}
        if 'github' in url:
            headers = {"Authorization": "token {}".format(token)}
    else:
        headers = None
    r = requests.get(url, stream=True, headers=headers)
    with open(fpath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*64):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return fpath


def backupfilter(tarinfo):
    if ('__pycache__' not in tarinfo.name) and \
       ('src' not in tarinfo.name) and \
       ('.git' not in tarinfo.name) and \
       ('.cache' not in tarinfo.name) and \
       ('.pyc' not in tarinfo.name):
        return tarinfo


def filtered(names, blacklist):
    """Filter the list of file or directory names."""
    rv = names[:]
    for pattern in blacklist:
        rv = [n for n in rv if not fnmatch.fnmatch(n, pattern)]
    return rv


def zip(target_dir, zip_file, blacklist=None):  # pylint: disable=W0622
    """Zip the given directory, write to the given zip file."""
    if not os.path.isdir(target_dir):
        raise IOError('%s does not exist!' % target_dir)
    blacklist = blacklist or []
    with zipfile.ZipFile(zip_file, mode='a') as z:
        for r, d, f in os.walk(target_dir, topdown=True):
            d[:] = filtered(d, blacklist)
            for filename in filtered(f, blacklist):
                filepath = os.path.join(r, filename)
                zi = zipfile.ZipInfo(filepath, localtime(time()))
                zi.filename = os.path.relpath(filepath, target_dir)
                if '.py' in zi.filename:
                    zi.external_attr = 0o754 << 16
                elif not zi.filename.endswith('/'):
                    zi.external_attr = 0o644 << 16
                zi.compress_type = zipfile.ZIP_STORED
                with open(filepath, 'rb') as f:
                    content = f.read()
                z.writestr(zi, content)
            for dirname in d:
                dirpath = os.path.join(r, dirname)
                z.write(dirpath, os.path.relpath(dirpath, target_dir))


@listen_to('(.*)', re.IGNORECASE)
def catchall(message, text):
    """Process GitOps and custom messages.
    """
    if (os.environ['TARGET_DEVICE'] != 'all' and
       os.environ['TARGET_DEVICE'] != device_name):
        return
    try:
        scripts = open(base_dir + "/screenplays/aliases.yml", "r")
        acts = yaml.load_all(scripts)
        for act in acts:
            for alias, response in act.items():
                regexp = re.compile(alias)
                if regexp.search(text):
                    post = slackmq(os.environ['API_TOKEN'],
                                   message.body['channel'],
                                   message.body['ts'])
                    if not post.ack():
                        return
                    chat.post(response)
                    post.unack()
                    return
    except Exception:
        pass
    mbody = message.body
    if text == 'git pull':
        mbody = {'attachments': [{'text': 'passed'}]}
    elif not text == '':
        return
    list_ = ['passed', 'pushed to']
    try:
        if not any(word in mbody['attachments'][0]['text'] for word in list_):
            return
    except Exception:
        return

    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'],
                   message.body['ts'])
    if not post.ack():
        return

    if 'gitlab' in mbody['attachments'][0]['text']:
        private_token = settings.servers.gitlab.token
        artifact_url = settings.servers.gitlab.artifact_url
        properties_url = settings.servers.gitlab.properties_url
    else:
        private_token = settings.servers.github.token
        artifact_url = settings.servers.github.artifact_url
        properties_url = settings.servers.github.properties_url
    message.send(':new: {}Downloading and updating Troupe'.format(debug) +
                 ' to the latest release')

    # Backup existing troupe dir and files
    with tarfile.open(base_dir + '/.cache/troupe-backup.tar', 'w') as tar:
        tar.add('.', recursive=True, filter=backupfilter)
    filename = base_dir + '/.cache/clone.zip'

    # Download the artifact from the git repo
    download_artifact(artifact_url, filename, private_token)
    # Extract it under the cache dir
    pzf = zipfile.PyZipFile(filename)
    namelist = pzf.namelist()
    artifact_dir = namelist[0]
    try:
        shutil.rmtree(base_dir + '/.cache/' + artifact_dir)
    except OSError:
        pass
    pzf.extractall(path=base_dir+'/.cache', members=namelist)

    download_artifact(properties_url, filename, private_token)
    # Extract it under the cache dir
    pzf = zipfile.PyZipFile(filename)
    namelist = pzf.namelist()
    props_dir = namelist[0]
    try:
        shutil.rmtree(base_dir + '/.cache/' + props_dir)
    except OSError:
        pass
    pzf.extractall(path=base_dir+'/.cache', members=namelist)

    os.chdir(base_dir + '/.cache/' + artifact_dir)
    for root, dirs, files in os.walk(base_dir + '/.cache/'):
        for dir in dirs:
            for name in glob.glob('{}/{}/*.py'.format(root, dir)):
                os.chmod(name, 0o740)
    with tarfile.open(base_dir + '/.cache/troupe-new.tar', 'w') as tar:
        tar.add('.', recursive=True,
                filter=backupfilter)
    os.chdir(base_dir + '/.cache/' + props_dir)
    with tarfile.open(base_dir + '/.cache/troupe-new.tar', 'a') as tar:
        tar.add('.', recursive=True,
                filter=backupfilter)
    os.chdir(base_dir)

    with tarfile.open(base_dir + '/.cache/troupe-new.tar') as tar:
        tar.extractall(path=base_dir)

    with open(nextlaunch, 'w') as launch_file:
        launch_file.write("Updated Troupe on {device_name}. " +
                          "Approve this with a :thumbsup:\n")
        launch_file.write("canary {device_name}")
    chat.post("relaunch {}".format(device_name))
    post.unack()


@listen_to('^promote (.*)', re.IGNORECASE)
@listen_to('^upload (.*)', re.IGNORECASE)
def upload(message, target_device=None):
    if target_device == device_name:
        slack = Slacker(os.environ['API_TOKEN'])
        filename = base_dir + '/.cache/troupe-new.tar'
        response = slack.files.upload(
            filename, channels=[os.environ['CHANNEL_NAME']],
            title='troupe-new.tar',
            initial_comment='uploading {} tarball'.format(device_name)
        )
        sleep(1)
        url = response.body['file']['url_private_download']
        last_download = base_dir + '/.last_download'
        with open(last_download, 'w') as last_file:
            print(url, file=last_file)
        chat.post('rollout {}'.format(url))


def check_dependencies(message, requirement_file_name):
    """
    Checks to see if the python dependencies are fullfilled.
    Debug is enabled during updates.
    """
    dependencies = []
    session = pip.download.PipSession()
    for req in parse_requirements(requirement_file_name, session=session):
        try:
            pkg_resources.require(str(req.req))
        except VersionConflict as e:
            project_name = pkg_resources.get_distribution(e.dist).project_name
            message.send(':snake: [{}] Upgrading Python package {}'
                         .format(device_name, project_name))
            try:
                os.system('pip3 install --upgrade {}'.format(project_name))
            except Exception:
                message.send(':warning: I had a problem installing {} on {}'
                             .format(project_name, device_name))
        except DistributionNotFound as e:
            project_name = pkg_resources.get_distribution(e.dist).project_name
            message.send(':snake: [{}] Installing Python package {}'
                         .format(device_name, project_name))
            try:
                os.system('pip3 install {}'.format(project_name))
            except Exception:
                message.send(':warning: I had a problem installing {} on {}'
                             .format(project_name, device_name))
        if req.req is not None:
            dependencies.append(str(req.req))
        else:
            pass


@listen_to('^relaunch$', re.IGNORECASE)
@listen_to('^relaunch (.*)', re.IGNORECASE)
def relaunch(message, target_device=all):
    """Restart Troupe, install any Python dependencies along the way
    """
    if target_device == 'all' or target_device == device_name:
        args = sys.argv[:]
        sleep(5)
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]
        sleep(10)
        os.chdir(base_dir)
        check_dependencies(message, base_dir + '/requirements.txt')
        os.execv(sys.executable, args)


@listen_to('^sync (.*)', re.IGNORECASE)
@listen_to('^rollout (.*)', re.IGNORECASE)
def sync(message, url):
    """Recursively download Troupe from Slack files, unpack it
       and restart itself.
    """
    last_download = base_dir + '/.last_download'
    touch(last_download)
    url = url.replace('<', '')
    url = url.replace('>', '')
    if url not in open(last_download).read():
        post = slackmq(os.environ['API_TOKEN'],
                       message.body['channel'],
                       message.body['ts'])
        if not post.ack():
            return
        sleep(rate_limit)
        message.send('['+device_name+'] Performing a rolling update...')
        filename = url.rsplit('/', 1)[-1]
        if url.startswith('http'):
            download_file(url, base_dir + '/.cache/' + filename,
                          os.environ['API_TOKEN'])
        with tarfile.open(base_dir + '/.cache/' + filename) as tar:
            tar.extractall(path=base_dir)
        with open(last_download, 'w') as last_file:
            print(url, file=last_file)
        with open(nextlaunch, 'w') as launch_file:
            print("rollout {}".format(url), file=launch_file)
        post.unack()
        relaunch(message, device_name)
    else:
        return


@on_reaction('+1')
@on_reaction('-1')
def reactops(message):
    channel = message.body['message']['item']['channel']
    timestamp = message.body['message']['item']['ts']
    reaction = message.body['message']['reaction']
    token = settings.servers.devops.oauth_token
    response = topic.history(token, channel, timestamp)
    history_post = response.json()['messages'][0]['text']

    # Ignore retracted reactions
    try:
        response.json()['messages'][0]['reactions']
    except Exception:
        return

    # do something when post is approved or rejected
    if 'Updated Troupe on ' in history_post:
        if history_post.split()[3][:-1] == device_name:
            if reaction == '+1':
                chat.post('target all')
                chat.post('promote {}'.format(history_post.split()[3][:-1]))
            elif reaction == '-1':
                chat.post(':back: Reverting to previous version.')
                with tarfile.open(base_dir +
                                  '/.cache/troupe-backup.tar') as tar:
                    tar.extractall(path=base_dir)
                chat.post('relaunch {}'.format(device_name))


@listen_to('^canary (.*)$', re.IGNORECASE)
@listen_to('^target (.*)$', re.IGNORECASE)
def target(message, target_device=all):
    """Designate a Troupe bot device to handle requests.
    """
    post = slackmq(os.environ['API_TOKEN'],
                   message.body['channel'], message.body['ts'])
    os.environ['TARGET_DEVICE'] = target_device
    if not post.ack():
        return
    message.send(':baby_chick: {}Commands will run on {}.'
                 .format(debug, target_device))
    post.unack()
