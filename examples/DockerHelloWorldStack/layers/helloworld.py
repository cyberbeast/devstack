from devstack.layer import Layer


class HelloWorld(Layer):
    def shared_config(self):
        return {}

    def prop_init(self):
        self.logger = self.shared_ref.logger

    def deploy(self):
        self.shared_ref.update_stack_status(
            self.__class__.__name__,
            status='From deploy() method in HelloWorld')
        return self.run_cmd(
            command='docker run -d hello-world',
            continue_on_error=False,
            logger=self.logger)

    def destroy(self):
        self.shared_ref.update_stack_status(
            self.__class__.__name__,
            status='From destroy() method in HelloWorld')
        return self.run_cmd(
            command=
            "docker stop $(docker ps -a | grep -m 1 hello-world | awk '{print $12}')",
            continue_on_error=False)
