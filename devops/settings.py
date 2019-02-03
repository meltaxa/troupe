import os
import sys
import yaml
from attrdict import AttrMap

current_dir = os.path.dirname(os.path.abspath(__file__))
with open(current_dir + '/settings.yml', 'r') as stream:
    config = yaml.load(stream)
    sys.modules[__name__] = AttrMap(config)
