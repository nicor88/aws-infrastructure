import boto3
import argparse
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_argparser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--stack-name',
                        required=True,
                        help='Cloudformation Stack Name'
                        )
    return parser

if __name__ == "__main__":
    args = create_argparser().parse_args()
    stack_name = vars(args).get('stack_name')
    logger.info('Deleting Stack {} in 60 seconds'.format(stack_name))
    time.sleep(60)
    cfn = boto3.client('cloudformation')
    cfn.delete_stack(StackName=stack_name)
