import boto3
import json

aws_lambda = boto3.client('lambda')
function_name = 'delete_cfn_stack'
stack_name = 'test'
res = aws_lambda.invoke(FunctionName=function_name,
                            Payload=json.dumps({'stack_name': stack_name}))
print(res['Payload'].read().decode())

res = aws_lambda.invoke_async(FunctionName=function_name,
                              InvokeArgs=json.dumps({'stack_name': stack_name}))

