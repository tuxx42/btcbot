#!/usr/bin/env python3

import cmd
import os
import readline
import kraken
import btce
import exsimu
import atexit
import depth_monitor
import configparser
import shlex
import logging

from depth import depth
from keymgt import KeyMgmt
from global_vars import gv

logging.basicConfig(filename='/tmp/bot.log',
                    level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)d %(levelname)s' +
                    '%(module)s - %(funcName)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger('cli')

version = "0.1 beta"
prompt = "(Cmd)"
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
    def __init__(self):
        self.depth_monitor_list = []
        cmd.Cmd.__init__(self)
        self.intro = "Welcome to Bot console!"
        readline.clear_history()
        self.depth_monitor_id = 0
        try:
            readline.read_history_file(histfile)
        except:
            pass
        atexit.register(readline.write_history_file, histfile)
        self.config = configparser.ConfigParser()
        self.configfile = '/tmp/bot.conf'
        try:
            self.config.read(self.configfile)
            global gv
            gv.update(dict(self.config['global_vars']))
        except:
            pass
        self.prompt = gv["prompt"] + ' '

    def save_config(self):
        with open(self.configfile, 'w') as f:
            self.config.write(f)

    def do_stop_depth_monitor(self, line):
        """stop_depth_monitor
        start the depth monitor"""
        try:
            for i in self.depth_monitor_list:
                if int(i['id']) == int(line):
                    print("stopping depth monitor %s" % line)
                    i['object'].stop()
                    self.depth_monitor_list.remove(i)
                    break
        except:
            pass

    def do_get_balance(self, line):
        api1 = gv['api1']
        b = markets[api1].get_balance()
        print(repr(b))

    def do_start_depth_monitor(self, line):
        """start_depth_monitor <api1> <api2>
        start the depth monitor"""
        api1 = gv['api1']
        api2 = gv['api2']
        s = ('starting depth monitor between "%s" and "%s"' % (api1, api2))
        sm = depth_monitor.SpreadMonitor(
            markets[api1],
            markets[api2],
            gv['pair'],
            gv['depth_interval']
        )
        print(s)
        sm.setDaemon(True)
        sm.start()
        self.depth_monitor_list.append({'id': self.depth_monitor_id,
                                        'object': sm,
                                        'api1': api1,
                                        'api2': api2})
        self.depth_monitor_id += 1

    def do_show_depth_monitors(self, line):
        """show_depth_monitors
        show a list of all active depth monitors"""
        for item in self.depth_monitor_list:
            print("id=%d, %s/%s" % (item['id'], item['api1'], item['api2']))

    def do_show_globals(self, line):
        """show_globals
        shows all global variable settings"""
        pad = max(len(x) for x in gv.keys())
        for i in sorted(gv.keys()):
            print("%*s: '%s'" % (- (pad + 3), i, gv[i]))

    def do_unset_globals(self, line):
        """unset_global <global_var> [<global_var> ... <global_var>]
        unsets a global variable"""
        for i in line.split():

            global gv
            if i in gv.keys():
                print("removing key:", i)
                del gv[i]
                self.config['global_vars'] = gv
                self.save_config()
            else:
                print("invalid key:", line)

    def do_set_globals(self, line):
        """set_global <global_var=value>
        set global variable to a new value"""
        try:
            d = dict([t.split('=') for t in shlex.split(line)])
        except Exception as e:
            print(e)
            return
        global gv
        gv.update(d)
        self.config['global_vars'] = gv
        if "prompt" in gv.keys():
            self.prompt = gv['prompt'] + ' '
        self.save_config()

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
        api1 = gv['api1']
        api2 = gv['api2']
        print("showing profitable orders between '%s' and '%s'" % (api1, api2))
        r = depth.profitable_orders(
            markets[api1].depth(), markets[api2].depth(),
            markets[api1].fees, markets[api2].fees,
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
            exec(line)
        except Exception as e:
            print(e.__class__, ":", e)

    def emptyline(self):
        """Do nothing on empty line input"""
        pass

    def precmd(self, line):
        return line

    def complete_profitable_orders(self, text, line, start_index, end_index):
        return ['kraken', 'btc-e']

    def complete_set_globals(self, text, line, start_index, end_index):
        if text:
            return [
                gvar for gvar in gv.keys()
                if gvar.startswith(text)
            ]
        else:
            return list(gv.keys())

    def complete_unset_global(self, text, line, start_index, end_index):
        return self.complete_set_global(text, line, start_index, end_index)


def main():
    completer = cmd_completer()
    log.info('Enter main event loop')
    completer.cmdloop()
    readline.write_history_file(histfile)

if __name__ == "__main__":
    main()
