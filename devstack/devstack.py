import sys
from terminaltables import SingleTable
from devstack.utils import clear_screen
import logging, json
from PyInquirer import prompt, print_json, Separator


class DevStack():
    def __init__(self):
        self.registered_layers = {}
        self.registered_modes = {}
        self.layer_dependency_graph = {}
        self.stack_status = {}
        self.stack_mode_status = {}
        self.stack_toggle_status = {}
        self.initialize_logger()
        self.initialize_stack_table()

    def initialize_logger(self, loglevel='INFO'):
        logging.basicConfig(
            level=loglevel,
            format='%(levelname)-8s %(message)s',
            datefmt='%m-%d-%y %H:%M') # Define a standard logging configuration for the Deployment class.
        self.logger = logging.getLogger(__name__) # Define a logging interface for the Deployment class.

    def initialize_stack_table(self):
        self.stack = [['LAYER',' ', 'STATUS']]
        self.stack_table = SingleTable(self.stack)
        for i in range(1, 3):
            self.stack_table.justify_columns[i] = 'center'
        self.stack_table.inner_row_border = True

    def add_layer(self, layer_cls):
        layer_object = layer_cls()
        self.logger.info(f'Registering Layer: {layer_cls.__name__} \t {layer_object}')
        # print(f'Depends_on: {layer_object.depends_on}')
        self.registered_layers[layer_cls.__name__] = layer_object
        if hasattr(layer_object, 'depends_on') is not False:
            self.layer_dependency_graph[layer_cls.__name__] = layer_object.depends_on
        else:
            self.layer_dependency_graph[layer_cls.__name__] = (None,)

    def add_mode(self, mode_cls):
        mode_object = mode_cls()
        self.logger.info(f'Registering Mode: {mode_cls.__name__} \t {mode_object}')
        for k, v in mode_object.prepare_modes().items():
            self.registered_modes[k] = v
            self.stack_mode_status[k] = v

    def __order(self, arg):
        '''
            Simple Dependency resolver

        "arg" is a dependency dictionary in which
        the values are the dependencies of their respective keys.
        '''
        d = dict((k, set(arg[k])) for k in arg)
        r = []
        while d:
            # values not in keys (Layers without dependencies)
            t=set(i for v in d.values() for i in v)-set(d.keys())
            # and keys without value (Layers without dependencies)
            t.update(k for k, v in d.items() if not v)
            # can be done right away
            if not list(t):
                print("Dependency resolution failed.")
                sys.exit(1)
            for layer in t:
                if layer is not None:
                    r.append(layer)
            # and cleaned up
            d=dict(((k, v-t) for k, v in d.items() if v))
        for layer in r:
            self.stack_status[layer] = {
                'key': layer,
                'symbol': "◌",
                'status': "-"
            }
            self.stack.append([element for element in self.stack_status[layer].values()])
        return r
    
    def prompt_toggles(self, layer_ordered):
        if not self.load_config():
            for layer in self.registered_layers.keys():
                self.stack_toggle_status[layer] = False
        
        layer_list = [{'name': layer, 'checked': self.stack_toggle_status[layer]} for layer in layer_ordered]

        mode_list = [{'name': mode, 'checked': self.stack_mode_status[mode]} for mode in self.registered_modes.keys()]

        questions = [
            {
                'type': 'checkbox',
                'qmark': '⦾',
                'message': 'Configuration',
                'name': 'enabled',''
                'choices': [Separator('\n--LAYERS--')] + layer_list + [Separator('\n--MODES--')] + mode_list,
            }
        ]

        answers = prompt(questions)
        enabled_options = answers['enabled'].copy()
        print(f"RESRES {enabled_options}")
        for option in enabled_options:
            if option in self.registered_modes.keys():
                self.stack_mode_status[option] = True
                enabled_options.remove(option)


        for layer in layer_ordered:
            self.stack_toggle_status[layer] = False

        for layer in enabled_options:
            self.stack_toggle_status[layer] = True
            self.update_stack_status(layer, symbol='◌', status='Pending')

        self.logger.debug(f'Toggles: {self.stack_toggle_status}')
        self.logger.debug(f'Modes: {self.stack_mode_status}')

        self.update_config_file()

        return answers

    def resolve(self):
        return self.__order(self.layer_dependency_graph)

    def show_stack(self):
        clear_screen()
        print(self.stack_table.table)

    def update_stack_status(self, layer, symbol=None, status=None):
        if layer not in self.stack_status.keys():
            self.stack_status[layer] = {}

        if symbol is not None:
            self.stack_status[layer]['symbol'] = symbol
        
        if status is not None:
            self.stack_status[layer]['status'] = status

        # print(self.stack)
        for idx in range(1, len(self.stack)):
            if self.stack[idx][0] == layer:
                self.stack[idx] = [layer, self.stack_status[layer]['symbol'], self.stack_status[layer]['status']]
        self.show_stack()

    def load_config(self):
        try:
            with open(f'.{self.name}.json') as f:
                temp = json.load(f)
        except FileNotFoundError:
            self.logger.warn(f"Config file for {self.name} does not exist. Loading defaults.")
            return False

        self.stack_toggle_status = temp['stack_toggle_status']
        self.stack_mode_status = temp['stack_mode_status']
        
        return True

    def update_config_file(self):
        temp = {
            'stack_toggle_status': self.stack_toggle_status,
            'stack_mode_status': self.stack_mode_status
        }
        with open(f'.{self.name}.json', 'w') as f:
            json.dump(temp, f)
        self.logger.info(f'Writing to config: .{self.name}.json')

    def deploy(self, loglevel="INFO", name='DEFAULT'):
        self.name = name
        print(loglevel)
        logging.getLogger().setLevel(loglevel)

        self.stack_table.title = self.name + ' Stack'
        order = self.resolve()

        enabled = self.prompt_toggles(order)['enabled']
        self.show_stack()

        for layer in order:
            if layer is not None and layer in enabled:
                self.update_stack_status(layer, symbol='...', status='🤞 Executing')
                ret_code = self.registered_layers[layer].execute()

                if ret_code == 0:
                    self.update_stack_status(layer, symbol="✔", status='👍 Deployed')
                else:
                    self.update_stack_status(layer, symbol="❌", status="👎 Failed")
                    

devstack = DevStack()
