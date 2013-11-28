"""
Simple Flask Webapp to receive Trello Webhook API callbacks and Post to
a HipChat room.

Copyright 2013 Valentin v. Seggern <valentin.vonseggern@telekom.de>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import logging
import hmac
from hashlib import sha1
from base64 import b64encode
from ConfigParser import ConfigParser
from threading import Thread

from flask import Flask
from flask import request
from werkzeug.exceptions import Unauthorized

import hipchat
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

config = ConfigParser()
config.read('trello-hipchat.cfg')

@app.route('/board_modified', methods=['POST', 'HEAD'])
def board_modified():
    if 'HEAD' in request.method:
        logger.debug('Trello is checking us out... Well - hello there!')
        return "Welcome dear Trello..."
    # The registration HEAD for some reason does not come with a verification header...
    try:
        verify_request()
    except Unauthorized, e:
        logger.warning('Request could not be authenticated. Possible attack event. Headers: %s. Data: %s',
            request.headers, request.data)
        raise e

    payload = json.loads(request.data)
    if 'updateCard' in payload['action']['type']:
            handle_card_update(payload['action'])
    return 'Thanks, Trello...'

def verify_request():
    secret = config.get('trello', 'secret')
    cb = config.get('integration', 'callback_url')
    raw = request.data + cb
    mac = hmac.new(secret, raw, sha1)
    h = b64encode(mac.digest()).lower()
    request_header = request.headers.get('x-trello-webhook', 'no such header').lower()

    if h != request_header:
        raise Unauthorized()

def handle_card_update(action):
    logger.info('handling card update: %s', json.dumps(action, indent=4))
    parsed = parse(action)
    if parsed:
        notify_hipchat('%(name)s just %(action)s %(item)s' % (parsed))

def parse(action):
    try:
        list_after = action['data']['listAfter']['id']
        list_before = action['data']['listBefore']['id']
        parsed = {}
        if config.get('trello', 'list_todo') in list_after:
            parsed['action'] = 'put back'
        if config.get('trello', 'list_in_progress') in list_after:
            parsed['action'] = 'started working on'
        if config.get('trello', 'list_done') in list_after:
            parsed['action'] = 'finished'
        parsed['name'] = action['memberCreator']['fullName']
        parsed['item'] = action['data']['card']['name']
        return parsed
    except KeyError, e:
        logger.debug("""Got a KeyError (%s) while parsing request from Trello.
            Probably this was not a move card event...""", e)

def notify_hipchat(msg):
    logger.debug('Sending "%s" to hipchat' % msg)
    hipster = hipchat.HipChat(token=config.get('hipchat', 'token'))
    hipster.message_room(config.get('hipchat', 'room'), config.get('hipchat', 'sender'), msg)

@app.before_first_request
def init():
    # Run the init in another thread so that the other endpoints can answer.
    Thread(target=register_at_trello).start()

def register_at_trello():
    create_webhook = {
        'idModel': config.get('trello', 'board_id'),
        'callbackURL': config.get('integration', 'callback_url')
    }
    headers = {'content-type': 'application/json'}

    endpoint = 'https://api.trello.com/1/token/%s/webhooks?key=%s' % \
        (config.get('trello', 'token'), config.get('trello', 'key'))

    payload = json.dumps(create_webhook, indent=4)
    logger.debug('Posting to %s: %s', endpoint, payload)

    resp = requests.put(endpoint, data=payload, headers=headers)

    if resp.status_code == 200:
        logger.info('GREAT SUCCESS... Registering webhook at trello worked.')
        return True
    logger.error('Failed to register at trello with HTTP %s: %s', resp.status_code, resp.text)
    return False