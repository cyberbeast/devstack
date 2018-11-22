"""
.. package:: DevStack

.. packageauthor:: Sandesh Gade <sandesh.gade@gmail.com>
"""

import sys
from terminaltables import SingleTable
from devstack.utils import clear_screen
import logging, json
from PyInquirer import prompt, print_json, Separator


class DevStack():
    """DevStack Class

    A *DevStack* is an abstraction that represents a collection of *Layer* objects that make up a Stack and the associated methods for interacting with them.

    Attributes
    ----------

    registered_layers {}
        A dictionary interface where keys are the names of *Layers* that are registered at execution time and values are the callable instances of the *Layer* class.
    
    registered_modes {}
        A dictionary interface where keys are the names of *Modes* that are registered at execution time and the values are the callable instances of *Mode* class.
    
    layer_dependency_graph {}
        A dictionary that represents the dependencies between *Layers* of the stack. Each key is a *Layer* name and the corresponding value represents a set of it's dependencies. The graph is used to perform a topological sort to determine the ordering of the layers when deploying.
    
    stack_status {}
        A dictionary that represents the current status of each of the connstituent layers of a stack. The keys are the names of each registered *Layer* object and the values assume a dictionary structure with the following keys
        * Symbol - Represents the key that expresses the state of operations (Start, in-progress and done) for a layer. Supports unicode characters on compatible terminal environments.
        * Status - Represents a key that reflects the current state of the layer as a string message. Supports unicode characters on compatible terminal environments.

    stack_mode_status {}
        A dictionary interface that represents a user's preferences for a registered *Mode* as a boolean. Keys are names of *Mode* objects and values are the corresponding boolean values that reflect whether or not the user has enabled the resepective mode.

    stack_toggle_status {}
        A dictionary interface that represents a user's preferences for a registered *Layer* as a boolean. Keys are names of *Layer* objects and values are the corresponding boolean values that reflect whether a user has enabled the respective layer.

    shared_config {}
        A dictionary interface that contains:
        * *Prop* objects as *Prop*.name and *Prop*.value pairs.
        * Cross-layer shared properties that are defined as part of the *Layer*'s shared_config method.

    registry_logs []
        A list containing log entries for the *Layer*, *Mode* and *Prop* registration mechanisms.

    Methods
    -------
    deploy()
        Deploys the layers of the stack in topological ordering of their respective dependencies according to the preferences decided by the user (toggles and modes)
    

        
    """

    def __init__(self):
        self.registered_layers = {}
        self.registered_modes = {}
        self.layer_dependency_graph = {}
        self.stack_status = {}
        self.stack_mode_status = {}
        self.stack_toggle_status = {}
        self.shared_config = {}
        self.__initialize_logger()
        self.__initialize_stack_table()
        self.registry_logs = []

    def __initialize_logger(self, loglevel='INFO'):
        logging.basicConfig(
            level=loglevel,
            format='%(levelname)-8s %(message)s',
            datefmt='%m-%d-%y %H:%M'
        )  # Define a standard logging configuration for the Deployment class.
        self.logger = logging.getLogger(
            __name__)  # Define a logging interface for the Deployment class.

    def __initialize_stack_table(self):
        self.stack = [[' ', 'LAYER', 'STATUS', ' ']]
        self.stack_table = SingleTable(self.stack)
        for i in range(1, 3):
            self.stack_table.justify_columns[i] = 'center'
        self.stack_table.inner_row_border = True

    def add_prop(self, prop_cls):
        prop_object = prop_cls()
        self.registry_logs.append(
            f'{"Registering Prop":18}: {prop_cls.__name__:>15} ─> {prop_object}'
        )
        self.shared_config[prop_object.name] = prop_object.values

    def add_layer(self, layer_cls):
        layer_object = layer_cls()
        self.registry_logs.append(
            f'{"Registering Layer":18}: {layer_cls.__name__:>15} ─> {layer_object}'
        )
        # print(f'Depends_on: {layer_object.depends_on}')
        self.registered_layers[layer_cls.__name__] = layer_object
        if hasattr(layer_object, 'depends_on') is not False:
            self.layer_dependency_graph[layer_cls.
                                        __name__] = layer_object.depends_on
        else:
            self.layer_dependency_graph[layer_cls.__name__] = (None, )

    def add_mode(self, mode_cls):
        mode_object = mode_cls()
        self.registry_logs.append(
            f'{"Registering Mode":18}: {mode_cls.__name__:>15} ─> {mode_object}'
        )
        self.registered_modes[mode_object.name] = mode_object
        self.stack_mode_status[mode_object.name] = mode_object.default

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
            t = set(i for v in d.values() for i in v) - set(d.keys())
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
            d = dict(((k, v - t) for k, v in d.items() if v))
        for layer in r:
            self.stack_status[layer] = {
                'symbol': "◌",
                'key': layer,
                'status': "-"
            }
            self.stack.append(
                [element for element in self.stack_status[layer].values()])
            print(self.stack)
        return r

    def prompt_toggles(self, layer_ordered):
        if not self.load_config():
            for layer in self.registered_layers.keys():
                self.stack_toggle_status[layer] = False

        layer_list = [{
            'name': layer,
            'checked': self.stack_toggle_status[layer]
        } for layer in layer_ordered]

        mode_list = [{
            'name': mode,
            'checked': self.stack_mode_status[mode]
        } for mode in self.registered_modes.keys()]

        questions = [{
            'type':
            'checkbox',
            'qmark':
            '⦾',
            'message':
            'Configuration',
            'name':
            'enabled',
            ''
            'choices': [Separator('\n--LAYERS--')] + layer_list +
            [Separator('\n--MODES--')] + mode_list,
        }]

        answers = prompt(questions)
        enabled_options = answers['enabled'].copy()
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

    def update_stack_status(self,
                            layer,
                            symbol=None,
                            status=None,
                            additional=[]):

        if layer not in self.stack_status.keys():
            self.stack_status[layer] = {}

        if symbol is not None:
            self.stack_status[layer]['symbol'] = f'{symbol:^3}'

        if status is not None:
            self.stack_status[layer]['status'] = f'{status:^50}'

        for idx in range(1, len(self.stack)):
            if self.stack[idx][1] == layer:
                if len(additional) >= 1:
                    more = [element for element in additional]
                else:
                    more = self.stack[idx][3:]
                self.stack[idx] = [
                    self.stack_status[layer]['symbol'], layer,
                    self.stack_status[layer]['status']
                ] + more
        self.show_stack()

    def load_config(self):
        try:
            with open(f'.{self.name}.json') as f:
                temp = json.load(f)
        except FileNotFoundError:
            self.logger.warn(
                f"Config file for {self.name} does not exist. Loading defaults."
            )
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

    def destroy(self):
        pass

    def deploy(self, loglevel="INFO", name='DEFAULT'):
        """Deploys the layers of the stack in tolopogical ordering of their corresponding dependencies.

        Parameters
        ----------
        loglevel: str
            Sets the verbosity for logger interface
        
        name: str
            Sets the name for the DevStack
        """
        self.name = name  # Initialize name
        logging.getLogger().setLevel(
            loglevel)  # Set log level to the user defined choice
        self.logger.debug(
            '\n\t' + '\n\t'.join(self.registry_logs) +
            '\n')  # Output the registry logs on the debug channel.
        self.stack_table.title = self.name + ' Stack'  # Set the name of the stack_table

        order = self.resolve(
        )  # Generate the correct ordering of layers to satisfy dependencies between them

        for layer in order:  # For each layer in the topological ordering of the layers
            self.shared_config[layer] = self.registered_layers[
                layer].shared_config(
                )  # Call the Layer's shared_config() method to populate the share_config attribute

        for layer in order:  # For each layer in the topological ordering of the layers
            self.registered_layers[layer].prop_init(
            )  # Call the Layer's prop_init() method to prepare each layer's initializing properties.

        if not logging.getLogger().isEnabledFor(
                logging.DEBUG):  # Check if the loglevel is set to DEBUG.
            clear_screen()  # If not, clear the screen

        enabled = self.prompt_toggles(
            order
        )['enabled']  # Get a list of Layer names which the user has enabled as input.

        self.show_stack()  # Print the current stack.

        for layer in order:  # For each layer in the topological ordreing of the layers
            if layer is not None and layer in enabled:  # If the layer is enabled
                self.update_stack_status(
                    layer, symbol='...', status=' 🤞 Deploying Layer'
                )  # Update status to reflect that it is being processed.
                ret_code = self.registered_layers[layer].deploy(
                )  # Call the layer's deploy method and await the return code

                if ret_code == 0:  # If return code is 0 (deploy method executed without errors)
                    self.update_stack_status(
                        layer, symbol="✔", status=' 👍 Layer is up.'
                    )  # Then update the layer status to reflect that the layer is up.
                elif ret_code < 0:  # Else if the return code is negative (deploy method returned errors)
                    self.update_stack_status(
                        layer, symbol="❌", status=" 👎 Failed"
                    )  # Then update the layer status to reflect that the process failed.
                else:  # In all other cases
                    self.update_stack_status(
                        layer, symbol="✔", status="Complete"
                    )  # Update the layer status as Complete.


devstack = DevStack()
