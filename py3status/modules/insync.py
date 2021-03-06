# -*- coding: utf-8 -*-

"""
Gets the current insync status

Configuration parameters:
    format: Display format to use *(default
        '{status} {queued}'
        )*

Format status string parameters:
    {status} Status of Insync
    {queued} Number of files queued

@author Joshua Pratt <jp10010101010000@gmail.com>
Thanks to @author Iain Tatch <iain.tatch@gmail.com> for the script that this is based on
@license BSD
"""

from time import time
import subprocess


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    format = '{status} {queued}'

    def check_insync(self, i3s_output_list, i3s_config):
        status = str(subprocess.check_output(["/usr/bin/insync", "get_status"]))
        if len(status) > 5:
            status = status[2:-3]
        color = i3s_config.get('color_degraded', '')
        if status == "OFFLINE":
            color = i3s_config.get('color_bad', '')
        if status == "SHARE":
            color = i3s_config.get('color_good', '')
            status = "INSYNC"

        queued = str(subprocess.check_output(["/usr/bin/insync", "get_sync_progress"]))
        queued = queued.split("\\n")
        if len(queued) > 2 and "queued" in queued[-2]:
            queued = queued[-2]
            queued = queued.split(" ")[0].replace("b'", "")
        else:
            queued = ""
        results = self.format.format(status=status, queued=queued)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': results,
            'color': color
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.check_insync([], config))
        sleep(1)
