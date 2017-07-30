import boto3
import argparse
import logging
import time
import json

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
    sleep_time = 30
    logger.info('Deleting Stack {} in {} seconds'.format(stack_name,sleep_time))
    time.sleep(sleep_time)
    aws_lambda = boto3.client('lambda')
    function_name = 'delete_cfn_stack'
    res = aws_lambda.invoke(FunctionName=function_name,
                            Payload=json.dumps({'stack_name': stack_name}))
    logger.info(res['Payload'].read().decode())

