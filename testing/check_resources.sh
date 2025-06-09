# check_resources.sh
#!/bin/bash

echo "Checking ScamVanguard AWS Resources..."
echo "======================================"

echo -e "\n📋 Lambda Functions:"
aws lambda list-functions --query "Functions[?contains(FunctionName, 'ScamVanguard')].FunctionName" --output table

echo -e "\n📢 SNS Topics:"
aws sns list-topics --query "Topics[?contains(TopicArn, 'scamvanguard')]" --output table

echo -e "\n💾 DynamoDB Tables:"
aws dynamodb list-tables --query "TableNames[?contains(@, 'ScamVanguard')]" --output table

echo -e "\n📧 SES Verified Identities:"
aws ses list-identities --output table

echo -e "\n🪣 S3 Buckets:"
aws s3 ls | grep scamvanguard
