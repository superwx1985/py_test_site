config_dict = dict()
config_dict['config'] = None


def get_config():
    return config_dict['config']


def set_config(config):
    config_dict['config'] = config
