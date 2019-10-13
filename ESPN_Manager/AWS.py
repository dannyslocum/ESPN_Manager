import json
import boto3

# Create CloudWatchEvents client
cloudwatch_events = boto3.client('events')

# Put an event rule
response = cloudwatch_events.put_rule(
    Name='test',
    ScheduleExpression='cron(*/5 * * * ? *)',
    State='ENABLED',
    Description='test description',
    RoleArn='arn:aws:lambda:us-east-2:534552671502:function:test'
)
print(response['RuleArn'])


# Create CloudWatchEvents client
cloudwatch_events = boto3.client('events')

# Put target for rule
response = cloudwatch_events.put_targets(
    Rule='default',
    Targets=[
        {
            'Arn': 'arn:aws:lambda:us-east-2:534552671502:function:test',
            'Id': 'test',
            'Input': json.dumps({"max": 1000})
        }
    ]
)
print(response)
