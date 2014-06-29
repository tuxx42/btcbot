#!/usr/bin/env python3

import atexit
import readline
import signal
import sys
import os
#import plot
import kraken
import btce
import exsimu
#import cryptsy
import time
import threading
from depth import depth

version = "0.1 beta"
prompt = "bot > "
histfile = "/tmp/history"
usage = {'exit': 'exit terminal',
         'help': 'show this message',
         'version': 'show version',
         'echo': 'echo messsage',
         'showmods': 'show modules',
         'load': 'load module',
         'plot': 'plot data',
         'kraken.get_balance': 'get balance from kraken',
         'kraken.get_depth': 'get depth from kraken',
         'kraken.print_depth': 'get depth from kraken',
         'kraken.add_order': 'add an order in kraken',
         'spread': 'get spread e.g: bot> spread api1=btce api2=kraken',
         'btce.add_order': 'add an order in btc-e',
         'btce.get_balance': 'get balance from btc-e',
         'btce.get_depth': 'get depth from btc-e',
         'btce.print_depth': 'get depth from btc-e',
         'exsimu.add_order': 'add an order in btc-e',
         'exsimu.get_balance': 'get balance from simulator',
         'exsimu.get_depth': 'get depth from simulator',
         'exsimu.print_depth': 'get depth from simulator',
         }


def get_depth(callback, callback_args, interval):
    while True:
        callback(**callback_args)
        time.sleep(interval)


def start_depth_thread(api):
    t = threading.Thread(target=get_depth,
                         args=[api.get_depth, {}, 1])
    t.setDaemon(True)
    t.start()


markets = {
    'kraken': kraken.kraken('foobox'),
    'btce': btce.btce(),
    'exsimu': exsimu.exsimu(),
}
#   'cryptsy': cryptsy_api,

markets['kraken'].decipher_key('kraken.enc')


class Cli:
    matches = []
    completions = {}
    values = []

    def __init__(self, histfile, values=None):
        readline.clear_history()
        try:
            readline.read_history_file(histfile)
        except:
            pass
        atexit.register(readline.write_history_file, histfile)
        readline.set_completer(self.completer)
        readline.parse_and_bind('tab: menu-complete')
        self.append_values(values)

    def append_values(self, appendix):
        self.values += appendix

    def completer(self, text, state):
        try:
            self.matches = self.completions[text]
        except KeyError:
            self.matches = [value for value in self.values
                            if text.upper() in value.upper()]
            self.completions[text] = self.matches
        try:
            return self.matches[state]
        except IndexError:
            return None


class MethodDispather():
    #plot = plot.Plot()

#    def depth(self):
#        print('Kraken')
#        print('------')
#        print(kraken.kraken.current_depth[-1])
#
#        print('btce')
#        print('------')
#        print(btce.btce.current_depth[-1])

    def spread(self, **kwargs):
        kwargs.setdefault('pair', 'btc_eur')
        params = {}
        try:
            params['api1'] = markets[kwargs['api1']]
            params['api2'] = markets[kwargs['api2']]
            params['pair'] = kwargs['pair']
        except Exception as e:
            raise Exception('unknown key', e)
        try:
            s = depth.spread(**params)
            if len(s.keys()):
                print('Marketspread: '
                      'volume(%s), profit(%s), buy(%s), sell(%s)' %
                      (s['volume'], s['profit'],
                       s['buy'].name, s['sell'].name))
        except Exception as e:
            print (e)
            pass

    def exit(self, params=None):
        print ('goodbye.')
        sys.exit(1)

    def version(self, params=None):
        print (version)

    def help(self, params=None):
        i = max(len(x) for x in usage.keys())
        for val in sorted(usage.keys()):
            s = '   %-' + str(i + 3) + 's:     %s'
            print (s % (val, usage[val]))

    def echo(self, params=None):
        print (params)

    def plot(self, params=None):
        print ('plotting %s' % params)

    def load(self, params=None):
        name = "package." + params[0]
        print ('trying to import', params[0])
        mod = __import__(name, fromlist=[])
        if mod:
            print ("worked!")

    def showmods(self, params=None):
        lst = os.listdir("modules")
        dir = []
        for d in lst:
            s = os.path.abspath("modules") + os.sep + d
            if os.path.isdir(s) and os.path.exists(s + os.sep + "__init__.py"):
                dir.append(d)
        for d in dir:
            print ('modules.' + d)
            #res[d] = __import__("modules." + d, fromlist=["*"])

    def call(self, params=None):
        try:
            modulefunc = params[0].split('.')
            if len(modulefunc) > 1:
                params[0] = params[0].split('.', 1)[1]
                methodToCall = getattr(markets[modulefunc[0]], params[0])
            else:
                methodToCall = getattr(self, params[0])
        except IndexError as e:
            print(e)
            print ('unknown command')
            return None
        except Exception as e:
            print(e)
            print (params[0], 'unknown command')
            return None

        param_dict = dict(map(lambda t: tuple(t.split('=')), params[1:]))
        try:
            r = methodToCall(**param_dict)
            if r:
                print(r)
        except Exception as e:
            print(e)

    def __init__(self, values):
        self.values = values


def handler(signum, frame):
    print ('Signal handler called with signal', signum)
    print ('Hit Ctrl-D to exit')


def main():
    start_depth_thread(markets['kraken'])
    start_depth_thread(markets['btce'])

    cli = Cli(histfile, usage.keys())
    methods = MethodDispather(cli.values)

    signal.signal(signal.SIGINT, handler)

    while 1:
        a = input(prompt)
        try:
            params = a.split(' ')
            while '' in params:
                params.remove('')

            methods.call(params)
        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    main()
