"""Optional Linux test: python3-gi + dbus, only in a disposable build container.
Mocks ScreenCast, transfers a real socket FD, then closes the fake remote.
No screen capture, game process or running desktop session is used.
"""
import os
import socket
import subprocess
import sys
import time

import gi
from gi.repository import Gio, GLib

XML = '''<node>
<interface name="org.freedesktop.portal.ScreenCast">
<method name="CreateSession"><arg type="a{sv}" direction="in"/><arg type="o" direction="out"/></method>
<method name="SelectSources"><arg type="o" direction="in"/><arg type="a{sv}" direction="in"/><arg type="o" direction="out"/></method>
<method name="Start"><arg type="o" direction="in"/><arg type="s" direction="in"/><arg type="a{sv}" direction="in"/><arg type="o" direction="out"/></method>
<method name="OpenPipeWireRemote"><arg type="o" direction="in"/><arg type="a{sv}" direction="in"/><arg type="h" direction="out"/></method>
</interface>
<interface name="org.freedesktop.portal.Session"><method name="Close"/></interface>
</node>'''
PORTAL_PATH = '/org/freedesktop/portal/desktop'
SESSION = PORTAL_PATH + '/session/mock'
info = Gio.DBusNodeInfo.new_for_xml(XML)
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
              'RequestName', GLib.Variant('(su)', ('org.freedesktop.portal.Desktop', 0)),
              None, Gio.DBusCallFlags.NONE, 2000, None)

assert subprocess.run([sys.argv[1], '--check-runtime'], capture_output=True).returncode == 0

for mode in ('numeric', 'serial', 'cancel'):
    methods = []
    peers = []
    def handler(connection, sender, object_path, interface, method, params, invocation):
        methods.append(method)
        args = params.unpack()
        if method == 'Close':
            invocation.return_value(GLib.Variant('()', ()))
            return
        if method == 'OpenPipeWireRemote':
            assert args[0] == SESSION
            client, peer = socket.socketpair()
            fds = Gio.UnixFDList.new(); index = fds.append(client.fileno())
            invocation.return_value_with_unix_fd_list(GLib.Variant('(h)', (index,)), fds)
            client.close(); peers.append(peer)
            # A real PipeWire server isn't required: close the transferred socket
            # to exercise connect_fd failure and bounded orderly cleanup.
            GLib.timeout_add(100, lambda: (peer.close(), False)[1])
            return
        options = args[-1]
        if method == 'SelectSources':
            assert options['types'] == 1 and options['multiple'] is False
        request = PORTAL_PATH + '/request/' + options['handle_token']
        invocation.return_value(GLib.Variant('(o)', (request,)))
        response = 1 if mode == 'cancel' and method == 'SelectSources' else 0
        results = {}
        if method == 'CreateSession':
            results['session_handle'] = GLib.Variant('s', SESSION)
        if method == 'Start':
            props = {'source_type': GLib.Variant('u', 1)}
            if mode == 'serial': props['pipewire-serial'] = GLib.Variant('t', 12345)
            results['streams'] = GLib.Variant('a(ua{sv})', [(93, props)])
        def respond():
            connection.emit_signal(sender, request, 'org.freedesktop.portal.Request',
                                   'Response', GLib.Variant('(ua{sv})', (response, results)))
            return False
        GLib.timeout_add(10, respond)
    objects = [bus.register_object(PORTAL_PATH, info.interfaces[0], handler, None, None),
               bus.register_object(SESSION, info.interfaces[1], handler, None, None)]
    child = subprocess.Popen([sys.argv[1]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 20
    while child.poll() is None and time.monotonic() < deadline:
        while GLib.MainContext.default().pending(): GLib.MainContext.default().iteration(False)
        time.sleep(0.01)
    if child.poll() is None:
        child.kill(); raise AssertionError('helper did not terminate after mock remote failure')
    stdout, stderr = child.communicate()
    assert not stdout, 'diagnostics must not contaminate binary frame stdout'
    assert methods[-1] == 'Close', methods
    if mode == 'cancel':
        assert methods == ['CreateSession', 'SelectSources', 'Close'], methods
        assert child.returncode == 3
    else:
        assert methods == ['CreateSession', 'SelectSources', 'Start', 'OpenPipeWireRemote', 'Close'], methods
        assert child.returncode != 0
        assert ("companion_selector=" + mode).encode() in stderr
        assert b"event=core.connected" in stderr, stderr.decode()
    for obj in objects: bus.unregister_object(obj)
    print(mode + ': portal methods, response handling, FD transfer and session cleanup passed')
