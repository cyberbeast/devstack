# DevStack
A Micro Framework for Development Stacks.

#### What is DevStack?
Ever find yourself running tons of bash/powerline/perl/ruby/_{insert_tool_here}_ scripts to deploy your development stack? DevStack provides an implementation agnostic interface to managing your development stack scripts so that you can build tools to automate your stack deployments. 

#### Why I created DevStack?
I am working on a project at work to automate our stack deployment down to a "single-click" solution. My boss had previously crafted an impressive _bash_ automation which achieved that. However, I felt that it lacked certain features. I added a few improvements to that utility combining the features of [dialog](https://manpages.debian.org/testing/dialog/dialog.1.en.html) and [Associative Arrays](https://www.gnu.org/software/bash/manual/html_node/Arrays.html) in _bash_. However, it soon got too "_hacky_" and cumbersome to manage. Also, _bash_ scripts aren't the easiest to read through when trying to understand what it does. This motivated me to move to a _python_ port of the script. The level of versatility that _python_ provided to the script was unparalleled. After a couple rounds of feedback, I decided to implement a framework that establishes the following ideals:

* **Abstraction** of a set of bash commands as a _Development Stack (DevStack)_ and the logical constituents as a _Layer_ of the stack.
* **Separation of Concerns** - Framework Interface is made aware of Layer definitions at runtime.
* **Shared Configuration** for Layers of a Stack - _Layers_ can share properties.
* **Persistant Configuration** - Maintain a state of the previous settings for the Stack to improve developer usability.
* **Monitor** - Always keep the developer informed of the state of the stack.




## Requirements

Use `pip install` to install the following:-

* `terminaltables`
* `pyinquirer`

## Framework Architecture

![Framework Architecture](https://www.lucidchart.com/publicSegments/view/99579cc8-7b9a-4622-9797-25576a25a189/image.png)
