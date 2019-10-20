import numpy as np
import os
import yaml
import logging
from collections import OrderedDict


class OrderedEasyDict(OrderedDict):
    """Using OrderedDict for the `easydict` package
    See Also https://pypi.python.org/pypi/easydict/
    """

    def __init__(self, d=None, **kwargs):
        super(OrderedEasyDict, self).__init__()
        if d is None:
            d = OrderedDict()
        if kwargs:
            d.update(**kwargs)
        for k, v in d.items():
            setattr(self, k, v)
        # Class attributes
        for k in self.__class__.__dict__.keys():
            if not (k.startswith('__') and k.endswith('__')):
                setattr(self, k, getattr(self, k))

    def __setattr__(self, name, value):
        # special handling of self.__root and self.__map
        if name.startswith('_') and (name.endswith('__root') or name.endswith('__map')):
            super(OrderedEasyDict, self).__setattr__(name, value)
        else:
            if isinstance(value, (list, tuple)):
                value = [self.__class__(x)
                         if isinstance(x, dict) else x for x in value]
            else:
                value = self.__class__(value) if isinstance(value, dict) else value
            super(OrderedEasyDict, self).__setattr__(name, value)
            super(OrderedEasyDict, self).__setitem__(name, value)

    __setitem__ = __setattr__


__C = OrderedEasyDict()
cfg = __C  # type: OrderedEasyDict()

# Random seed
__C.SEED = None

# Dataset name
# Used by symbols factories who need to adjust for different
# inputs based on dataset used. Should be set by the script.
__C.DATASET = None

# Project directory, since config.py is supposed to be in $ROOT_DIR/nowcasting
__C.ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

__C.MNIST_PATH = os.path.join(__C.ROOT_DIR, 'moving_mnist_pp')
# if not os.path.exists(__C.MNIST_PATH):
#     os.makedirs(__C.MNIST_PATH)
# __C.HKO_DATA_BASE_PATH = os.path.join(__C.ROOT_DIR, 'hko_data')

__C.MOVINGMNIST = OrderedEasyDict()
__C.MOVINGMNIST.DISTRACTOR_NUM = 0
__C.MOVINGMNIST.VELOCITY_LOWER = 0.0
__C.MOVINGMNIST.VELOCITY_UPPER = 3.6
__C.MOVINGMNIST.SCALE_VARIATION_LOWER = 1  # 1/1.1
__C.MOVINGMNIST.SCALE_VARIATION_UPPER = 1  # 1.1
__C.MOVINGMNIST.ROTATION_LOWER = 0  # -30
__C.MOVINGMNIST.ROTATION_UPPER = 0  # 30
__C.MOVINGMNIST.ILLUMINATION_LOWER = 0.6
__C.MOVINGMNIST.ILLUMINATION_UPPER = 1.0
__C.MOVINGMNIST.DIGIT_NUM = 1
__C.MOVINGMNIST.IN_LEN = 10
__C.MOVINGMNIST.OUT_LEN = 10
__C.MOVINGMNIST.TESTING_LEN = 20
__C.MOVINGMNIST.IMG_SIZE = 64
__C.MOVINGMNIST.TEST_FILE = os.path.join(__C.MNIST_PATH, "movingmnist_10000_nodistr.npz")


def _merge_two_config(user_cfg, default_cfg):
    """ Merge user's config into default config dictionary, clobbering the
        options in b whenever they are also specified in a.
        Need to ensure the type of two val under same key are the same
        Do recursive merge when encounter hierarchical dictionary
    """
    if type(user_cfg) is not OrderedEasyDict:
        return
    for key, val in user_cfg.items():
        # Since user_cfg is a sub-file of default_cfg
        if not key in default_cfg:
            raise KeyError('{} is not a valid config key'.format(key))

        if (type(default_cfg[key]) is not type(val) and
                default_cfg[key] is not None):
            if isinstance(default_cfg[key], np.ndarray):
                val = np.array(val, dtype=default_cfg[key].dtype)
            else:
                raise ValueError(
                     'Type mismatch ({} vs. {}) '
                     'for config key: {}'.format(type(default_cfg[key]),
                                                 type(val), key))
        # Recursive merge config
        if type(val) is OrderedEasyDict:
            try:
                _merge_two_config(user_cfg[key], default_cfg[key])
            except:
                print('Error under config key: {}'.format(key))
                raise
        else:
            default_cfg[key] = val


def cfg_from_file(file_name, target=__C):
    """ Load a config file and merge it into the default options.
    """
    import yaml
    with open(file_name, 'r') as f:
        print('Loading YAML config file from %s' %f)
        yaml_cfg = OrderedEasyDict(yaml.load(f))

    _merge_two_config(yaml_cfg, target)


def ordered_dump(data, stream=None, Dumper=yaml.SafeDumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items(), flow_style=False)

    def _ndarray_representer(dumper, data):
        return dumper.represent_list(data.tolist())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    OrderedDumper.add_representer(OrderedEasyDict, _dict_representer)
    OrderedDumper.add_representer(np.ndarray, _ndarray_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


def save_cfg(dir_path, source=__C):
    cfg_count = 0
    file_path = os.path.join(dir_path, 'cfg%d.yml' %cfg_count)
    while os.path.exists(file_path):
        cfg_count += 1
        file_path = os.path.join(dir_path, 'cfg%d.yml' % cfg_count)
    with open(file_path, 'w') as f:
        logging.info("Save YAML config file to %s" %file_path)
        ordered_dump(source, f, yaml.SafeDumper, default_flow_style=None)


def load_latest_cfg(dir_path, target=__C):
    import re
    cfg_count = None
    source_cfg_path = None
    for fname in os.listdir(dir_path):
        ret = re.search('cfg(\d+)\.yml', fname)
        if ret != None:
            if cfg_count is None or (int(re.group(1)) > cfg_count):
                cfg_count = int(re.group(1))
                source_cfg_path = os.path.join(dir_path, ret.group(0))
    cfg_from_file(file_name=source_cfg_path, target=target)
