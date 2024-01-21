# Copyright (c) 2024 Seweryn Rusecki
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from libqtile.command.base import expose_command
from libqtile.widget import base

if TYPE_CHECKING:
    from typing import Any, Callable


class Touchpad(base.ThreadPoolText):
    """
    A simple widget to display touchpad state.

    You can also bind keyboard shortcuts to the Touchpad widget with:

    .. code-block:: python

        Key(
            [],
            "XF86TouchpadToggle",
            lazy.widget["touchpad"].toggle()
        )
    """

    device_id: None | str
    get_state_func: None | Callable[[str], bool]
    set_state_func: None | Callable[[str, bool], None]

    defaults: list[tuple[str, Any, str]] = [
        (
            "device_id",
            None,
            "Touchpad name or id, provided as ``str``. "
            "It set to ``None`` the widget will try to find it automatically using ``xinput``.",
        ),
        (
            "get_state_func",
            None,
            "Function which can read the touchpad state. "
            "It should return the state as ``bool``. "
            "It set to ``None`` a default function based on ``xinput`` will be used.",
        ),
        (
            "set_state_func",
            None,
            "Function which can enable/disable touchpad. "
            "It should take one ``bool`` parameter and change touchpad state accordingly. "
            "It set to ``None`` a default function based on ``xinput`` will be used.",
        ),
        ("format", "{state}", "Displayed text format"),
        ("enabled_char", "[👆]", "State shown when touchpad is enabled"),
        ("disabled_char", "[🚫]", "State shown when touchpad is disabled"),
        (
            "update_interval",
            10,
            "Seconds between status updates. "
            "When using ``toggle`` command from this class, the status is ",
        ),
    ]

    def __init__(self, **config) -> None:
        base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(Touchpad.defaults)

        self.add_callbacks(
            {
                "Button1": self.toggle,
            }
        )

    def _configure(self, qtile, bar) -> None:
        base.ThreadPoolText._configure(self, qtile, bar)

    def poll(self) -> str:
        if self.device_id is None:
            device_id = self._get_touchpad_device_name()
        if self.get_state_func is None:
            get_state_func = self._get_touchpad_enabled

        state = get_state_func(device_id)
        state_text = self.enabled_char if state else self.disabled_char
        return self.format.format(state=state_text)

    @expose_command()
    def toggle(self) -> None:
        """Toggle touchpad on/off."""

        if self.device_id is None:
            device_id = self._get_touchpad_device_name()
        if self.get_state_func is None:
            get_state_func = self._get_touchpad_enabled
        if self.set_state_func is None:
            set_state_func = self._set_touchpad_enabled

        new_state = not get_state_func(device_id)
        set_state_func(device_id, new_state)
        self.force_update()

    @staticmethod
    def _get_touchpad_device_name() -> str:
        properties = subprocess.check_output(["xinput", "list", "--name-only"], text=True)

        for line in properties.splitlines():
            if "touchpad" in line.lower():
                return str(line)

        raise RuntimeError("Could not determine touchpad name automatically!")

    @staticmethod
    def _get_touchpad_enabled(device_id: str) -> bool:
        properties = subprocess.check_output(["xinput", "list-props", device_id], text=True)

        for line in properties.splitlines():
            if "device enabled" in line.lower():
                return line[-1] == "1"

        raise RuntimeError("Could not determine touchpad state automatically!")

    @staticmethod
    def _set_touchpad_enabled(device_id: str, state: bool) -> None:
        subprocess.run(["xinput", "enable" if state else "disable", device_id])
