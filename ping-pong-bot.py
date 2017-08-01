#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
import re
import os

from slackclient import SlackClient

BOT_ID = os.environ.get('BOT_ID')
BOT_NICKNAME = 'ping-pong-bot2'
BOT_AT = '<@' + BOT_ID + '>'

COMMAND_PREFIX = '!'
HELP_COMMAND = 'help'
INVITE_COMMAND = 'invite'
TOP_COMMAND = 'top'
ALL_COMMAND = 'all'

CHANNEL_ID = 'C5LF6UTEU'

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

channel_profiles = {}


def handle_command(command, channel, current_user):
    response = u"Ja neatceries kā lietot botu, raksti @" + BOT_NICKNAME + " *" \
               + HELP_COMMAND + '*.'
    user_input = command.split()

    if len(user_input) == 1:
        if get_input_command(user_input, 0) == HELP_COMMAND:
            response = u"Pieejamās komandas:\n *- @" + BOT_NICKNAME + " " + HELP_COMMAND + "* | palīdzības komanda" \
                       + "\n *- @" + BOT_NICKNAME + " " + INVITE_COMMAND + "* | ielūgt nejaušu pretinieku" \
                       + "\n *- @" + BOT_NICKNAME + " " + INVITE_COMMAND + " @pretinieks* | ielūgt izvēlētu pretinieku" \
                       + "\n *- @" + BOT_NICKNAME + " " + TOP_COMMAND + " * | TOP 10 spēlētāju saraksts" \
                       + "\n *- @" + BOT_NICKNAME + " " + ALL_COMMAND + " * | visu spēlētāju saraksts"

        if get_input_command(user_input, 0) == INVITE_COMMAND:
            random_member_profile = get_random_member_profile(current_user)
            send_public_invitation(random_member_profile, channel, current_user)
            return

        if get_input_command(user_input, 0) == TOP_COMMAND:
            response = u"*TOP 10 Spēlētāji*"
            post_in_chat({"attachments": render_top_button(), "response": response, "channel": channel})
            return

        if get_input_command(user_input, 0) == ALL_COMMAND:
            response = u"*Visi spēlētāji*"
            post_in_chat({"attachments": render_top_button(True), "response": response, "channel": channel})
            return

    if len(user_input) == 2 and get_input_command(user_input, 0) == INVITE_COMMAND:
        member_profile = channel_profiles.get(re.sub('[<>@]', '', get_input_command(user_input, 1).upper()))

        if (member_profile['user']['id'] == current_user):
            response = 'Šis lietotājs nevar būt izaicināts!'
            post_in_chat({"attachments": '', "response": response, "channel": channel})
            return

        try:
            send_public_invitation(member_profile, channel, current_user)
        except:
            response = 'Nevarēju atrast lietotāju ar šādu vārdu vai arī lietotājs nav šī kanāla loceklis.'
            post_in_chat({"attachments": '', "response": response, "channel": channel})

        return

    post_in_chat({"attachments": '', "response": response, "channel": channel})


def get_channel_member_list():
    channel_information = slack_client.api_call('channels.info',
                                                channel=CHANNEL_ID)

    for member in channel_information['channel']['members']:
        member_profile = slack_client.api_call('users.info',
                                               user=member)
        channel_profiles[member] = member_profile


def post_in_chat(attributes):
    slack_client.api_call('chat.postMessage', link_names=1, attachments=attributes['attachments'],
                          channel=attributes['channel'], text=attributes['response'], as_user=True)


def get_input_command(commands, key):
    return commands[key].lower().strip()


def send_public_invitation(member, channel, current_user):
    name = member['user']['name']
    first_name = member['user']['profile']['first_name']
    last_name = member['user']['profile']['last_name']
    thumb_image = member['user']['profile']['image_72']

    response = u"Tavs nākamais upuris ir *" + first_name + ' ' \
               + last_name + ' @' + name \
               + '* :table_tennis_paddle_and_ball:'

    return post_in_chat({"attachments": render_invitation_buttons({'first_name': first_name,
                                                                   'name': name, 'thumb_image': thumb_image,
                                                                   'current_user': current_user}),
                         "response": response, "channel": channel})


def get_random_member_profile(current_user):
    member = pick_random_member_id()

    while member['presence'] == 'away' or member['id'] == current_user \
            or member['id'] == BOT_ID:
        member = pick_random_member_id()

    random_member_profile = channel_profiles.get(member['id'])

    return random_member_profile


def pick_random_member_id():
    profile = random.choice(list(channel_profiles.keys()))
    member_presence = slack_client.api_call('users.getPresence',
                                            user=profile)
    picked_member = {"id": profile, "presence": member_presence}

    return picked_member


def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output

    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and 'channel' in output \
                    and 'user' in output and BOT_AT in output['text']:
                return (output['text'
                        ].split(BOT_AT)[1].strip().lower(),
                        output['channel'], output['user'])

    return (None, None, None)

def parse_simple_slack_put(slack_rtm_output):
    output_list = slack_rtm_output

    if output_list and len(output_list) > 0:
        for output in output_list:
            if output \
                    and 'text' in output \
                    and 'channel' in output \
                    and 'user' in output \
                    and output['text'].find(COMMAND_PREFIX) == 0:
                return (output['text'].split(COMMAND_PREFIX)[1].strip().lower(), output['channel'], output['user'])

    return (None, None, None)


def render_invitation_buttons(attributes):
    user = channel_profiles.get(attributes['current_user'])
    current_user = user['user']['name']
    return [{
        'image_url': attributes['thumb_image'],
        'fallback': current_user,
        'callback_id': 'menu_options_2319',
        'color': '#3AA3E3',
        'fields': [{'title': attributes['first_name']
                             + ", vai Tu esi pietiekami drosmīgs/-a, lai piekristu?"
                       , 'short': 'true', 'value': "@" + current_user + " gaida Tavu apstiprinājumu!"}],
        'actions': [{
            'name': attributes['name'],
            'text': "Piekrītu",
            'style': 'primary',
            'type': 'button',
            'value': 'accept',
            'data_source': 'external'
        }, {
            'name': attributes['name'],
            'text': 'Atcelt',
            'style': 'danger',
            'type': 'button',
            'value': 'cancel',
            'data_source': 'external',
            'confirm': {
                'title': "Kāda būs Tava izvēle?",
                'text': "Vai tiešām vēlies atcelt spēli?",
                'ok_text': "Jā",
                'dismiss_text': "Nē",
            },
        }],
    }]


def render_top_button(all_names=False):
    return [{
        'fallback': 'Nevaru atrast informāciju',
        'callback_id': 'menu_options_2320' if not all_names else 'menu_options_2321',
        'color': '#3AA3E3',
        'actions': [{
            'name': 'top' if not all_names else 'all',
            'text': "Skatīt rezultātus",
            'style': 'primary',
            'type': 'button',
            'value': 'top' if not all_names else 'all',
            'data_source': 'external'
        }],
    }]


if __name__ == '__main__':
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print('Printful bot connected and running!')
        get_channel_member_list()
        print('Member profiles retrieved!')
        while True:
            textContent = slack_client.rtm_read();
            (command, channel, user) = parse_slack_output(textContent)
            if command and user and channel:
                handle_command(command, channel, user)
            # Try simple commands
            else:
                (command, channel, user) = parse_simple_slack_output(textContent)
                if command and user and channel:
                    handle_command(command, channel, user)

            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print('Connection failed. Invalid Slack token or bot ID?')
