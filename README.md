# How to write and Ansible Module

### Context
Ansible version

Tested with ansible versions:
* 2.4.2.0

Run playbook:

`ansible-playbook elasticsearch.yml`

**Summary**
1. [Where to store Ansible Module](#where-to-store-ansible-module)
   1. [The Location](#the-location)
      a. [Store module at server side](#store-module-at-server-side)
      b. [Store module at local side](#store-moduleat-local-side)
   2. [The Configuration](#the-configuration)
2. [How to start an Ansible Module](#how-to-start-an-ansible-module)
   1. [Behaviour](#behaviour)
      a. [Ansible running behaviour](#ansible-running-behaviour)
      b. [Ansible module behaviour](#anssible-module-behaviour)
   2. [People already wrote working things](#people-already-wrote-working-things)
     a. [Basic Template](#basic-template)
     b. [Arguments](#arguments)
     c. [Routing](#routing)
     d. [Check Mode](#check-mode)


## Where to store Ansible Module

Ansible modules can be stored everywhere. The ansible config file can define the path where are located the modules.
To be in a Good Practice way you can store them into /usr/share/ansible/modules but you can also store it in your Ansible Git repository.


### The Location

#### Store module at server side
Let's store the module in the Ansible installation directory /usr/share/ansible in a subdir module.

You might need to create the directory as root

`root@ansible $ mkdir /usr/share/ansible/modules`

#### Store module at local side
Not to be dependent of the server you can store modules at the same level where you run playbooks in a directory library.
`ansible@ansible $ mkdir ~/ansible-playbooks/library`


## The configuration
### Local module
If you locally store your modules (polaybooks directory) you don't have to configure Ansible behaviour.

### Server module
Otherwise you need to set up and fill the key library (category defaults) in the ansible config file /etc/ansible/ansible.cfg and store your module there.

`root@ansible $ sed "s|^#\(library *\)=.*|\1= /usr/share/ansible/modules|g" /etc/ansible/ansible.cfg`



## How to start an Ansible Module
### Behaviour
#### Ansible running behaviour
The way to write an Ansible Module force you to think in a different way tha usual development.
You must always know that you will have 3 states at the end of the run : 
* ok : Nothing has been done. No change encountered on server.
* changed : Things has changed. Anisble made modification on the server.
* fail : Something went wrong before normally ending the ansible task.

This is the minimum to know about Ansible behaviour.

#### Ansible module behaviour
Considering your module is accessible (local or server side) you need to know how ansible gets and interprets your module.
The module is called by its filename (without extension).
A script called library/mymodule.py will be called mymodule in an Ansible task.

Module :
`library/elasticsearch.py`

Task:
```
- name: Call mymodule
  elasticsearch:
```

### Don't start from scratch People wrote working things
I will quickly explain you how to start and what are the first steps to do.
Let's try to initiate an elasticsearch module to create indices.

#### Basic template

This a minimalist template called examply.py that will help you to correctly start.

`vi library/elasticsearch.py`

```
#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: elasticsearch
short_description: Elasticsearch ansible module
description: Elasticsearch ansible module
version_added: ""
author: ""
notes:
    - 
requirements:
    - 
options:
    - 
'''

class ElasticAnsibleModule(AnsibleModule):

  def __init__(self, *args, **kwargs):
    self._output = []
    self._facts = dict()
    super(ElasticAnsibleModule, self).__init__(*args, **kwargs)

  def process(self):
    try:
      changed = False

      self.exit_json(changed=changed,
                     ansible_facts={"elasticsearch": self._facts},
                     output=self._output)
    except Exception as e:
      self.fail_json(msg=(e.message, self._output))


def main():
  ElasticAnsibleModule(
  ).process()

if __name__ == '__main__':
  main()
```

Change a few things to stick to your module :
class ElasticAnsibleModule >>> class MymoduleAnsibleModule

Let's explain what's happening in the main :

`if __name__ == '__main__'` : Enter in this section when the script is run as an executable (and not a python module). The function main() will be call so.
  main()   : L

`def main()` : Let's enter in the main function
*  `ElasticAnsibleModule().process()`: Instanciate the class ElasticAnsibleModule and run the method process().

This is all what the main function must have.


Let's deep into the ElasticAnsibleModule class methods :
```
# ElasticAnsibleModule is an override of the class AnsibleModule. It keeps all its function, can add some and have its own methods (function of a class)
class ElasticAnsibleModule(AnsibleModule):

  # The constructor (__init__) is rewrited for the class ElasticAnsibleModule
  def __init__(self, *args, **kwargs):
    # We add some variables to better manage the behaviour of our module: output
    output = self._output = []
    # And here the ansible facts
    self._facts = dict()
    # We finally call the initial constructor to to inherit of all the power of the class AnsibleModule
    super(ElasticAnsibleModule, self).__init__(*args, **kwargs)


  # Define the method process()
  def process(self):
    # Begin a try/catch to better manage errors
    try:
      # Initiate the change (Remember ! The Ansible state) to False : Nothing has changed. This will allow us to easely manage the --check option
      changed = False

      # Success !! My task is finished ! Setting the state (changed) the fact (self._facts) and the output (self._output) owned by our class to the standard AnisbleModule state, facts and outputs
      self.exit_json(changed=changed,
                     ansible_facts={"elasticsearch": self._facts},
                     output=self._output)
    # In case of emergency
    except Exception as e:
      # Fail !! Something went wrong ! Print the message of the error (e.message) and the output to better debug (self._output)
      self.fail_json(msg=(e.message, self._output))
```

#### Arguments
The principle of ansible is to pass action to run. But what are action if they are immutable ? 
You can enter variable in your ansible task to allow Ansible module to be more dynamical.

But what are these said arguments ? I am sure you know :
Task :
```
  - name: Create indice test
    elasticsearch:
      url: 'http://elasticsearch.domain.fr:9200'
      type: indice
      indice_name: test
      state: present
```

We have 4 arguments : url, type, indice_name, state.

Now how to call them from my module ?
You will need to pass with the argument argument_spec into the class instanciation.

As everything is Yaml in plabooks we need to define the type of the entry between str, list. Type dict is defined by its structure.
```
def main():
  ElasticAnsibleModule(
    argument_spec=dict(
      url=dict(type='str', required=True),
      type=dict(type='str', required=True, choices=['indice', 'document']),
      indice_name=dict(type='str', required=True),
      state=dict(type='str', default='present', choices=['present','absent']),
    )
  ).process()
```

Now you call them in your process method. Let's see how !
```
  def process(self):
    try:
      changed = False

      # I want to use my parameter 'url'
      param_url = self.params['url']

      self.exit_json(changed=changed, ansible_facts={"elasticsearch": self._facts}, output=self._output)
    except Exception as e:
      self.fail_json(msg=(e.message, self._output))
```


#### Routing
We have a wonderful class and its strong method process. We now handle parameters from task to module.
It just left to make and run action using the parameters.

We need to identify the routing elements and the pure variables. 
Our module create indice in elasticsearch. For us routing will be defined by the type and the state parameters.
(This is an example to illustrate how to seprate Church from State)

So let's make a Route controller in the process methode and call the good method depending of the value our 2 routing parameters.

```
  def process(self):
    try:
      changed = False

      if self.params['type'] == 'indice':
        if self.params['state'] == 'present':
          changed |= self.elastic_indice_present(self.params['url'], self.params['indice_name'])
        elif self.params['state'] == 'absent':
          changed |= self.elastic_indice_absent(self.params['url'], self.params['indice_name'])
      else:
        unsupported_method(self)

      self.exit_json(changed=changed,
                     ansible_facts={"elasticsearch": self._facts},
                     output=self._output)
    except Exception as e:
      self.fail_json(msg=(e.message, self._output))
```

Router is done. Now let's code the functions behind.
```
  def elastic_indice_present(self, url, indice_name):
    req_headers = { "Content-type": "application/json" }
    req_url = "{}/{}" . format(url, indice_name)

    # Check if the willing indice does exist
    res_indice_check = requests.get(req_url, headers=req_headers)

    if res_indice_check.status_code in [404]: 
      # Means the indice does not exist so we can create it
      res_indice_add = requests.put(req_url, headers=req_headers)

      # Create a dict with some informations (status_code and a message)
      meta = dict(
        rc=res_indice_add.status_code,
        message="Indice '{}' has been created." . format(indice_name),
      )

      # Send the info dict to the output
      self._output = meta

      # Return True as "A changed has been done"
      return True

    elif res_indice_check.status_code in [200]:
      # Return False as "Nothing has changed"
      return False

    else:
      # You can informations like the result of your request
      self._output = dict(
        rc=res_indice_add.status_code,
      )
      # Handle unexpected behaviour : fatal return
      raise Exception("Something went wrong")
```


#### Check mode
We can handle the --check option in activating the attribute supports_check_mode=True in your class instanciation.
```
def main():
  ElasticAnsibleModule(
    argument_spec=dict(
      [...]
    ),
    supports_check_mode=True
  ).process()
```

And check to boolean status of the variable check_mode inside the class (test self.check_mode).
```
  def elastic_indice_present(self, indice_name):
    [...]
    # Stop if check_mode is true before doing any action
    if self.check_mode:
      return True
    [...]
```
