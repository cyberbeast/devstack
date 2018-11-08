from devstack.devstack import devstack
from subprocess import Popen, PIPE, STDOUT
import sys


class Registry(type):
    def __new__(cls, clsname, superclasses, attributedict):
        registry_methods = {
            'Layer': devstack.add_layer,
            'Mode': devstack.add_mode
        }
        # condition to prevent base class registeration
        # print(f'{cls}|\t{clsname}|\t{superclasses}|\t{attributedict}')
        attributedict['shared_ref'] = devstack
        newclass = type.__new__(cls, clsname, superclasses, attributedict)
        if superclasses:
            # print((superclasses[0].__name__))
            required_methods = ['execute'] if superclasses[0].__name__ == 'Layer' else ['prepare_modes']
            if not all(key in attributedict.keys() for key in required_methods):
                print(f'{clsname} does not contain either {" or ".join(required_methods)}')
                sys.exit(-2)
            registry_methods[superclasses[0].__name__](newclass)

        return newclass

class Layer(metaclass=Registry):
    def run_cmd(self, command):
        process = Popen(command, bufsize=0, stdout=PIPE, stderr=STDOUT, shell=True)
        
        while True:
            line = process.stdout.readline().rstrip()
            if not line:
                process.stdout.close()
                break;
            print(line.decode('utf-8'))
        process.wait()
        return process.returncode

class Mode(metaclass=Registry):
    pass