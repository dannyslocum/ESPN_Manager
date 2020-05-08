import json
import boto3


def save_file_to_s3(bucket, file_name, data):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, file_name)
    obj.put(Body=json.dumps(data))


def main():
    minute = '45'
    hour = '12'
    dayofmonth = '?'
    month = 'NOV-DEC'
    dayofweek = 'SUN'
    year = '2019'

    name = '{}_{}{}_{}'.format(dayofweek, hour, minute, year).replace(',', '.')
    schedule = 'cron({} {} {} {} {} {})'.format(minute, hour, dayofmonth, month, dayofweek, year)
    setup_cloudwatch_event(schedule, name)

    name = 'SUN_1550_2019'
    schedule = 'cron(50 15 ? NOV-DEC SUN 2019)'
    setup_cloudwatch_event(schedule, name)

    name = 'THU.SUN_1945'
    schedule = 'cron(45 19 ? NOV-DEC THU,SUN 2019)'
    setup_cloudwatch_event(schedule, name)


# Put an event rule
def setup_cloudwatch_event(schedule, name):
    # Create CloudWatchEvents client
    cloudwatch_events = boto3.client('events')
    print(schedule)

    response = cloudwatch_events.put_rule(
        Name=name,
        ScheduleExpression=schedule,
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
    return response


if __name__ == '__main__':
    main()