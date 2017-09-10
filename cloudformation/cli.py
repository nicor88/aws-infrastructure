import os
import argparse
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_argparser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--template-generator',
                        required=True,
                        help='Template generator file name'
                        )

    parser.add_argument('--action',
                        required=True,
                        choices=['create', 'delete', 'update'],
                        help='Action to execute'
                        )

    parser.add_argument('--aws-profile',
                        required=True,
                        help='Output path, can be file system or S3 bucket'
                        )

    return parser

if __name__ == "__main__":
    args = create_argparser().parse_args()
    template_generator = vars(args).get('template_generator')
    aws_profile = vars(args).get('aws_profile')
    action = vars(args).get('action')
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
    os.environ['AWS_PROFILE'] = aws_profile
    template_generator_path = os.path.join('cloudformation', 'template_generator',
                                           template_generator)
    file_to_execute = f'{template_generator_path}.py'

    exec(open(file_to_execute).read(), globals())

    if action == 'create':
        cfn.create_stack(**stack_args)
        logger.info('stack created')

    if action == 'update':
        cfn.update_stack(**stack_args)
        logger.info('stack updated')

    if action == 'delete':
        cfn.delete_stack(**stack_args)
        logger.info('stack deleted')
