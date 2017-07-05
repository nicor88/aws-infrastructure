import cfn_flip


def write_template(**stack_args):
    cfn_json_path = 'cloudformation/templates/json/{}.json'.format(stack_args['StackName'])
    cfn_yaml_path = 'cloudformation/templates/yaml/{}.yml'.format(stack_args['StackName'])
    with open(cfn_json_path, 'wt') as f:
        f.write(stack_args['TemplateBody'])
        print('wrote json template')
    with open(cfn_yaml_path, 'wt') as f:
        f.write(cfn_flip.to_yaml(stack_args['TemplateBody']))
        print('wrote yaml template')
