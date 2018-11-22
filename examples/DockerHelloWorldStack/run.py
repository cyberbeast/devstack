from devstack.devstack import devstack
from layers import *

devstack.deploy(loglevel='DEBUG', name='Docker Hello World')