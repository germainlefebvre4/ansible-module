#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule

import requests, json
import ast

DOCUMENTATION = '''
---
module: elasticsearch
short_description: Manage elasticsearch service
description:
    - Create, delete and rename an indice
    - Add a document to an indice
version_added: "0.1"
author: "Germain LEFEBVRE [INEAT]"
notes:
    - xxx
requirements:
    - requests
    - ast
options:
    url:
        description:
            - Elasticsearch service URL with protocol and port
        required: true
    type:
        description:
            - Type de entity to handle
        required: true
        choices:
            - indice
    indice_name:
        description:
            - Indice name
        required: true
    state:
        description:
            - Action to perform
        required: false
        default: present
        choices:
            - present
            - absent
'''


class ElasticAnsibleModule(AnsibleModule):

  def __init__(self, *args, **kwargs):
    self._output = []
    super(ElasticAnsibleModule, self).__init__(*args, **kwargs)


  def elastic_indice_present(self, indice_name):
    req_headers = { "Content-type": "application/json" }
    req_url = "{}/{}" . format(self.params['url'], indice_name)

    # Check if exists
    res_indice_check = requests.get(req_url, headers=req_headers)
    meta = dict(
      rc=res_indice_check.status_code,
    )


    if res_indice_check.status_code in [200]:
      # Already exists. Nothing to do
      self._output = meta
      return False
    else:
      if res_indice_check.status_code in [404]:
        # Create indice

        # Stop if check mode
        if self.check_mode:
          return True

        res_indice_add = requests.put(req_url, headers=req_headers)
        meta = dict(
          rc=res_indice_add.status_code,
          message="Indice '{}' has been created." . format(indice_name),
        )
        self._output = meta
        return True
      else:
        # Status code != 404. Unknown status. Throw error
        meta['message'] = "An error ocured. Check if the service is available. Use -vvv option to have more informations."
        self._output = meta
        raise Exception(meta['message'])


  def elastic_indice_rename(self, indice_name, name):
    req_headers = { "Content-type": "application/json" }
    req_url = "{}/_reindex" . format(self.params['url'])
    req_url_src = "{}/{}" . format(self.params['url'],indice_name)
    req_payload = dict(
      source=dict(
        index=indice_name,
      ),
      dest=dict(
        index=name,
        version_type='internal',
      ),
    )

    # Check if exists
    res_indice_src_check = requests.get(req_url_src, headers=req_headers)
    meta = dict(
      rc=res_indice_src_check.status_code,
    )

    if res_indice_src_check.status_code not in [200]:
      # Already exists. Nothing to do
      if res_indice_src_check.status_code in [404]:
        self._output = meta
        return False
      else:
        # Status code != 404. Unknown status. Throw error
        meta = dict(
          rc=res_indice_src_check.status_code,
          message="An error ocured. Check if the service is available. Use -vvv option to have more informations.",
        )
        self._output = meta
        raise Exception(meta['message'])
    else:
      # Rename indice

      # Stop if check mode
      if self.check_mode:
        return True

      res_indice_ren = requests.post(req_url, headers=req_headers, json=req_payload)
      meta = dict(
        rc=res_indice_ren.status_code,
        message="Indice '{}' has been renamed." . format(indice_name),
      )
      self._output = meta
      return True



  def elastic_indice_absent(self, indice_name):
    req_headers = { "Content-type": "application/json" }
    req_url = "{}/{}" . format(self.params['url'], indice_name)

    # Check if exists
    res_indice_check = requests.get(req_url, headers=req_headers)
    meta = dict(
      rc=res_indice_check.status_code,
    )

    # Check if indice does exist
    if res_indice_check.status_code not in [200]:
      if res_indice_check.status_code in [404]:
        # Already absent. Nothing to do
        self._output = meta
        return False
      else:
        # Status code != 404. Unknown status. Throw error
        meta = dict(
          rc=res_indice_check.status_code,
          message="An error ocured. Check if the service is available. Use -vvv option to have more informations.",
        )
        self._output = meta
        raise Exception(meta['message'])
    else:
      # Delete indice

      # Stop if check mode
      if self.check_mode:
        return True

      res_indice_del = requests.delete(req_url, headers=req_headers)
      meta = dict(
        rc=res_indice_del.status_code,
        message="Indice '{}' has been deleted." . format(indice_name),
      )
      self._output = meta
      return True


  def elastic_document_add(self, document, mapping_type):
    req_headers = { "Content-type": "application/json" }
    req_url = "{}/{}/{}/" . format(self.params['url'], self.params['indice_name'], mapping_type)
    req_url_check = "{}/{}" . format(self.params['url'], self.params['indice_name'])

    if type(document).__name__ == 'str':
      document = ast.literal_eval(document)

    # Check if exists
    res_indice_check = requests.get(req_url_check, headers=req_headers)
    meta = dict(
      rc=res_indice_check.status_code,
    )

    if res_indice_check.status_code in [200]:
      # Add document

      # Stop if check mode
      if self.check_mode:
        return True

      res_document_add = requests.post(req_url, headers=req_headers, json=document)
      if res_document_add.status_code in [201]:
        # Document added
        meta = dict(
          rc=res_document_add.status_code,
          message="Document added to indice '{}'." . format(self.params['indice_name']),
        )
        self._output = meta
        return True
      else:
        # Can't create document. Throw error
        meta = dict(
          rc=res_document_add.status_code,
          message="An error occured.",
          request=req_url,
          response=res_document_add.text,
        )
        self._output = meta
        raise Exception(meta['message'])
    else:
      # Service unavailable. Throw error
      meta = dict(
        rc=res_indice_check.status_code,
        message="An error occured. Check if the service is available.",
        request=req_url_check,
      )
      self._output = meta
      raise Exception(meta['message'])




  def process(self):
    try:
      changed = False
      # Initialize the result
      result = dict()

      if self.params['type'] == 'indice':
        if self.params['state'] == 'present':
          changed |= self.elastic_indice_present(self.params['indice_name'])
        elif self.params['state'] == 'absent':
          changed |= self.elastic_indice_absent(self.params['indice_name'])
        elif self.params['state'] == 'rename':
          changed |= self.elastic_indice_rename(self.params['indice_name'], self.params['rename'])
      elif self.params['type'] == 'document':
        changed |= self.elastic_document_add(self.params['document'], self.params['mapping_type'])

      self.exit_json(changed=changed,
                     #ansible_facts={self.params['indice_name']: self._facts},
                     output=self._output)

      # Return changing after run and throw error
    except Exception as e:
      self.fail_json(msg=(e.message, self._output))


def main():
  ElasticAnsibleModule(
    argument_spec=dict(
      url=dict(type='str', required=True),
      type=dict(type='str', required=True, choices=['indice', 'document']),
      indice_name=dict(type='str', required=True),
      mapping_type=dict(type='str', default='_doc'),
      rename=dict(type='str'),
      document=dict(type='str'),
      state=dict(type='str', default='present', choices=['present','absent','rename']),
    ),
    supports_check_mode=True
  ).process()

if __name__ == '__main__':
  main()
