version = "0.1 beta"
prompt = "(Cmd)"
histfile = "/tmp/history"


class global_vars(dict):
    def __init__(self, g_vars={}):
        self['api1'] = 'exsimu1'
        self['api2'] = 'exsimu2'
        self['prompt'] = prompt
        self['version'] = version
        self['histfile'] = histfile
        self['depth_interval'] = 2.0
        self['depth_timeout'] = 0.8
        self['depth_count'] = 20
        self['pair'] = 'btc_eur'
        self.update(g_vars)

gv = global_vars()
