from devstack.devstack import devstack
from subprocess import Popen, PIPE, STDOUT
import sys


class Registry(type):
    def __new__(cls, clsname, superclasses, attributedict):
        registry_methods = {
            'Layer': devstack.add_layer,
            'Mode': devstack.add_mode,
            'Prop': devstack.add_prop
        }

        required_methods = {
            'Layer': ['deploy', 'destroy', 'shared_config'],
            'Mode': ['default'],
            'Prop': ['name', 'values']
        }
        # condition to prevent base class registeration
        # print(f'{cls}|\t{clsname}|\t{superclasses}|\t{attributedict}')
        attributedict['shared_ref'] = devstack
        newclass = type.__new__(cls, clsname, superclasses, attributedict)
        if superclasses:
            # print((superclasses[0].__name__))
            required_methods = required_methods[superclasses[0].__name__]
            if not all(key in attributedict.keys() for key in required_methods):
                print(f'{clsname} does not contain either {" or ".join(required_methods)}')
                sys.exit(-2)
            registry_methods[superclasses[0].__name__](newclass)

        return newclass

class Layer(metaclass=Registry):
    def run_cmd(self, command, logger, continue_on_error=True, return_string=False):
        process = Popen(command, bufsize=0, stdout=PIPE, stderr=STDOUT, shell=True)

        if not return_string:
            logger.info(command)
            while True:
                line = process.stdout.readline().rstrip().decode('utf-8')
                if not line:
                    process.stdout.close()
                    break;
                if line.lower().startswith('error'):
                    logger.error(line)
                else:
                    logger.info(line)
            process.wait()

            # print(process.returncode)
            if process.returncode is not 0 and not continue_on_error:
                sys.exit(process.returncode)
            return process.returncode
        else:
            return process.communicate()[0].decode('utf-8')

class Mode(metaclass=Registry):
    pass

class Prop(metaclass=Registry):
    pass