import os
import boto3
import json
import requests
from datetime import datetime, timedelta, date

# 環境変数でSlackのWebhook URLを指定
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']


def lambda_handler(event, context) -> None:
    client = boto3.client('ce', region_name='us-east-1')

    # 合計とサービス毎の請求額を取得する
    total_billing = get_total_billing(client)
    service_billings = get_service_billings(client)

    # Slack用のメッセージを作成して送信
    (title, detail) = get_message(total_billing, service_billings)
    post_slack(title, detail)


def get_total_billing(client) -> dict:
    # 前日の範囲を取得
    (start_date, end_date) = get_total_cost_date_range()

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_cost_and_usage
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='DAILY',  # 前日分のみ取得
        Metrics=[
            'AmortizedCost'
        ]
    )
    return {
        'start': response['ResultsByTime'][0]['TimePeriod']['Start'],
        'end': response['ResultsByTime'][0]['TimePeriod']['End'],
        'billing': response['ResultsByTime'][0]['Total']['AmortizedCost']['Amount'],
    }


def get_service_billings(client) -> list:
    # 前日の範囲を取得
    (start_date, end_date) = get_total_cost_date_range()

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_cost_and_usage
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='DAILY',  # 前日分のみ取得
        Metrics=[
            'AmortizedCost'
        ],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    billings = []
    for item in response['ResultsByTime'][0]['Groups']:
        billings.append({
            'service_name': item['Keys'][0],
            'billing': item['Metrics']['AmortizedCost']['Amount']
        })
    return billings


def get_message(total_billing: dict, service_billings: list) -> (str, str):
    start = datetime.strptime(
        total_billing['start'], '%Y-%m-%d').strftime('%m/%d')
    end_yesterday = (datetime.strptime(
        total_billing['end'], '%Y-%m-%d') - timedelta(days=1)).strftime('%m/%d')
    total = round(float(total_billing['billing']), 2)

    title = f'{start}～{end_yesterday}の請求額は、{total:.2f} USDです。'
    details = []
    for item in service_billings:
        service_name = item['service_name']
        billing = round(float(item['billing']), 2)
        if billing > 0.0:
            details.append(f'　・{service_name}: {billing:.2f} USD')

    return title, '\n'.join(details)


def post_slack(title: str, detail: str) -> None:
    payload = {
        'attachments': [
            {
                'color': '#36a64f',
                'pretext': title,
                'text': detail
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        print(e)
    else:
        print(response.status_code)


def get_total_cost_date_range() -> (str, str):
    start_date = get_prev_day(1)  # 昨日の開始日
    end_date = get_today()        # 今日の日付（終了日）
    return start_date, end_date


def get_prev_day(prev: int) -> str:
    return (date.today() - timedelta(days=prev)).isoformat()


def get_today() -> str:
    return date.today().isoformat()
