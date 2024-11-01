# AWS COST DAILY SLACK NOTIFICATION

このリポジトリは前日分の AWS リソースのコストを Slack に通知するスクリプトです。

## セットアップ

CI をつくっていないのでローカルで Docker イメージのビルドとプッシュが必要です。

```bash
docker buildx build --platform linux/amd64 -f Dockerfile -t <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/aws-cost-daily-slack-notification:latest .
```

```bash
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com
```

```bash
docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/aws-cost-daily-slack-notification
```
