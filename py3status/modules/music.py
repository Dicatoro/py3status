# -*- coding: utf-8 -*-

"""
Display current song and control players.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (1h default)
    format: see placeholders below

    player_name: the name of the player. If empty then the player will be auto-detected

    format_down: text to display when there is no player detected
    color_down: color used to display `format_down` (red default)
    cache_timeout_down: time between two updates when there is no player detected (3 default)

    format_paused: text to display when the player is paused
    color_paused: color used to display `format_paused` (orange default)
    cache_timeout_paused: time between two updates when the player is paused (3 default)

    format_stopped: text to display when the player is stopped
    color_stopped: color used to display `format_stopped` ('#ff0000' default)
    cache_timeout_stopped: time between two updates when the player is stopped (3 default)

    format: text to display when the player is playing
    color: color used to display `format` ('#00ff00' default)
    cache_timeout: time between two updates when the player is playing (1 default)

    length_format: how `{length}` should be interpreted in `format` and
        `format_paused` ('{adapted}' default)
    position_format: how `{position}` should be interpreted in `format` and
        `format_paused` ('{adapted}' default)

    Controls:
        button_left 'toggle' default)
        button_right: ('stop' default)
        button_middle: ('' default)
        button_wheel_up: ('volume_up' default)
        button_wheel_down: ('volume_down' default)
        button_wheel_left: ('backward' default)
        button_wheel_right: ('forward' default)
        button_previous: ('previous' default)
        button_next: ('next' default)

    seek_offset: (5 default)
    volume_offset: (0.05 default)

Format of status string placeholders:
    {system} system/OS name, e.g. 'Linux', 'Windows', or 'Java'
    {node} computer’s network name (may not be fully qualified!)
    {release} system’s release, e.g. '2.2.0' or 'NT'
    {version} system’s release version, e.g. '#3 on degas'
    {machine} machine type, e.g. 'x86_64'
    {processor} the (real) processor name, e.g. 'amdk6'

@author Dicatoro
"""

from mpris2 import Player, get_players_uri
import dbus
import time


def get_elem(metadata, key, array_index):
    key = dbus.String(key)
    try:
        elem = metadata[key]
    except KeyError:
        return None
    if array_index is None:
        return elem
    return elem[array_index]


def player_info(metadata):
    info_params = {
        'artist': ('xesam:artist', 0),
        'title': ('xesam:title', None),
        'genre': ('xesam:genre', 0),
        'url': ('xesam:url', None),
        'length': ('mpris:length', None),
        'album': ('xesam:album', None),
    }

    info = {}
    for field_name, (key, array_index) in info_params.items():
        elem = get_elem(metadata, key, array_index)
        # fuck you dbus
        if isinstance(elem, dbus.String):
            elem = str(elem)
        elif isinstance(elem, (dbus.Int64, dbus.Int32, dbus.Int16)):
            elem = int(elem)
        elif isinstance(elem, dbus.Array):
            elem = list(elem)
        info[field_name] = elem
    return info


def convert_time(length):
    if length is None:
        length = 0
    tot_sec = length/1000000.0
    seconds = int(tot_sec % 60)

    tot_min = tot_sec/60.0
    minutes = int(tot_min % 60)

    tot_hours = tot_min/60.0
    hours = int(tot_hours % 60)

    adapted = '{:0>2}:'.format(hours) if hours else ''
    adapted += '{:0>2}:'.format(minutes) if hours else "{}:".format(minutes)
    adapted += '{:0>2}'.format(seconds)

    time_elements = {
        'tot_sec': tot_sec,
        'seconds': seconds,
        'tot_min': tot_min,
        'minutes': minutes,
        'tot_hours': tot_hours,
        'hours': hours,
        'adapted': adapted,
    }
    return time_elements


class Py3status:

    player_name = ''

    format_down = ''
    color_down = '#ff0000'
    cache_timeout_down = 3

    format_paused = '♪ {artist} - {title} - {position}/{length}'
    color_paused = '#ffcc00'
    cache_timeout_paused = 3

    format_stopped = '♪ Stopped'
    color_stopped = '#ff0000'
    cache_timeout_stopped = 3

    format = '♪ {artist} - {title} - {position}/{length}'
    color = '#00ff00'
    cache_timeout = 1

    length_format = '{adapted}'
    position_format = '{adapted}'

    button_left = 'toggle'
    button_right = 'stop'
    button_middle = ''
    button_wheel_up = 'volume_up'
    button_wheel_down = 'volume_down'
    button_wheel_left = 'backward'
    button_wheel_right = 'forward'
    button_previous = 'previous'
    button_next = 'next'

    seek_offset = 5
    volume_offset = 0.05

    def _get_player(self):
        if self.player_name:
            return 'org.mpris.MediaPlayer2.' + self.player_name

        # fetch all players
        players_uri = list(get_players_uri())
        if players_uri:
            return players_uri[0]
        return None

    def music(self):
        no_player = {
                'full_text': self.format_down,
                'cached_until': time.time()+self.cache_timeout_down,
                'color': self.color_down
            }

        player_uri = self._get_player()
        if player_uri is None:
            return no_player

        try:
            player = Player(dbus_interface_info={'dbus_uri': player_uri})
            metadata = player.Metadata
            playback_status = player.PlaybackStatus
            position = int(player.Position)
        except dbus.DBusException:
            return no_player

        info = player_info(metadata)

        length = convert_time(info['length'])
        info['length'] = self.length_format.format(**length)

        position = convert_time(position)
        info['position'] = self.position_format.format(**position)

        if playback_status == 'Playing':
            full_text = self.format.format(**info)
            return {
                'full_text': full_text,
                'cached_until': time.time()+self.cache_timeout,
                'color': self.color
            }
        elif playback_status == 'Paused':
            full_text = self.format_paused.format(**info)
            return {
                'full_text': full_text,
                'cached_until': time.time()+self.cache_timeout_paused,
                'color': self.color_paused
            }
        else:
            full_text = self.format_stopped.format(**info)
            return {
                'full_text': full_text,
                'cached_until': time.time()+self.cache_timeout_stopped,
                'color': self.color_stopped
            }

    def on_click(self, event):
        player_uri = self._get_player()
        if player_uri is None:
            return

        try:
            player = Player(dbus_interface_info={'dbus_uri': player_uri})
        except dbus.DBusException:
            return

        try:
            buttons = {
                1: 'left',
                2: 'middle',
                3: 'right',
                4: 'wheel_up',
                5: 'wheel_down',
                6: 'wheel_left',
                7: 'wheel_right',
                8: 'previous',
                9: 'next',
            }
            btn_name = buttons[event['button']]
            action = getattr(self, 'button_'+btn_name)
        except KeyError:
            return

        try:
            if action == 'play':
                player.Play()
            elif action == 'toggle':
                player.PlayPause()
            elif action == 'pause':
                player.Pause()
            elif action == 'stop':
                player.Stop()
            elif action == 'volume_up':
                player.Volume += self.volume_offset
            elif action == 'volume_down':
                player.Volume -= self.volume_offset
            elif action == 'next':
                player.Next()
            elif action == 'previous':
                player.Previous()
            elif action == "forward":
                player.Seek(self.seek_offset*1000000)
            elif action == "backward":
                player.Seek(-self.seek_offset*1000000)
        except dbus.DBusException:
            return

if __name__ == '__main__':
    print(Py3status().music())
