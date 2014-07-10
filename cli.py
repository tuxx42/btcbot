#!/usr/bin/env python3

import cmd
import os
import readline
import kraken
import btce
import exsimu
import atexit
from depth import depth
import depth_monitor
from keymgt import KeyMgmt
import configparser

import logging
logging.basicConfig(filename='/tmp/bot.log',
                    level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d %(levelname)s' +
                    '%(module)s - %(funcName)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger('cli')

version = "0.1 beta"
prompt = "(Cmd) "
histfile = "/tmp/history"


key_mgmt_kraken = KeyMgmt.from_file(
    'kraken.enc',
    password='foobox',
    padding=kraken.kraken.PADDING
)

key_mgmt_btce = KeyMgmt.from_file(
    'btce.enc',
    password='foobar',
    padding=kraken.kraken.PADDING
)
markets = {
    'kraken': kraken.kraken(key_mgmt_kraken),
    'btce': btce.btce(key_mgmt_btce),
    'exsimu1': exsimu.exsimu('data1', 'exsimu1'),
    'exsimu2': exsimu.exsimu('data2', 'exsimu2'),
}


class cmd_completer(cmd.Cmd):
    def __init__(self, prompt=None):
        self.depth_monitor_list = []
        cmd.Cmd.__init__(self)
        if prompt:
            self.prompt = prompt
        self.intro = "Welcome to Bot console!"
        readline.clear_history()
        try:
            readline.read_history_file(histfile)
        except:
            pass
        atexit.register(readline.write_history_file, histfile)
        self.config = configparser.ConfigParser()
        self.configfile = '/tmp/bot.conf'
        try:
            self.config.read(self.configfile)
            self.global_vars = dict(self.config['global_vars'])
        except:
            self.global_vars = {}
            self.global_vars['api1'] = "exsimu1"
            self.global_vars['api2'] = "exsimu2"

    def save_config(self):
        with open(self.configfile, 'w') as f:
            self.config.write(f)

    def do_stop_depth_monitor(self, line):
        """stop_depth_monitor
        start the depth monitor"""
        print("stopping depth monitor")
        self.sm.stop()

    def do_start_depth_monitor(self, line):
        """start_depth_monitor <api1> <api2>
        start the depth monitor"""
        print("starting depth monitor")
        self.sm = depth_monitor.SpreadMonitor(
            markets['kraken'],
            markets['btce'],
        )
        self.sm.setDaemon(True)
        self.sm.start()
#        self.depth_monitor_list.append(sm)

    def do_show_depth_monitors(self, line):
        """show_depth_monitors
        show a list of all active depth monitors"""
        for item in self.depth_monitor_list:
            print(item)

    def do_show_globals(self, line):
        """show_globals
        shows all global variable settings"""
        for i in self.global_vars.keys():
            print("%40s: %s" % (i, self.global_vars[i]))
        pass

    def do_set_global(self, line):
        """set_global <global_var>
        set global variable to a new value"""
        d = dict([t.split('=') for t in line.split()])
        self.global_vars.update(d)
        self.config['global_vars'] = self.global_vars
        self.save_config()
        pass

    def do_exit(self, line):
        """exit
        exit this shell. (Terminate)"""
        print ('goodbye.')
        return True

    def do_show_modules(self, params=None):
        """show_modules
        show a list of all available modules"""
        lst = os.listdir("modules")
        dir = []
        for d in lst:
            s = os.path.abspath("modules") + os.sep + d
            if os.path.isdir(s) and os.path.exists(s + os.sep + "__init__.py"):
                dir.append(d)
        for d in dir:
            print ('modules.' + d)
            #res[d] = __import__("modules." + d, fromlist=["*"])

    def do_profitable_orders(self, line):
        """profitable_orders <api1> <api2>
        show all profitable orders between api1 and api2"""
        print("showing profitable orders between %s and %s" %
              (self.global_vars['api1'], self.global_vars['api2']))
        r = depth.prof_orders(
            markets[self.global_vars['api1']].depth(),
            markets[self.global_vars['api2']].depth(),
            markets[self.global_vars['api1']].fees,
            markets[self.global_vars['api2']].fees,
        )
        print (repr(r))

    def do_EOF(self, line):
        """Ctrl-D
        Terminate this program"""
        print("GoodBye.")
        return True

    def do_version(self, line):
        """version
        show version string"""
        print(version)

    def default(self, line):
        try:
            exec(line) in self._locals, self._globals
        except Exception as e:
            print(e.__class__, ":", e)

    def emptyline(self):
        """Do nothing on empty line input"""
        pass

    def complete_profitable_orders(self, text, line, start_index, end_index):
        return ['kraken', 'btc-e']

    def complete_set_global(self, text, line, start_index, end_index):
        if text:
            return [
                    gvar for gvar in self.global_vars.keys()
                    if gvar.startswith(text)
                ]
        else:
            return list(self.global_vars.keys())


def main():
    completer = cmd_completer(prompt)
    log.info('Enter main event loop')
    completer.cmdloop()
    readline.write_history_file(histfile)

if __name__ == "__main__":
    main()
