# SlackLLM - A Slack Bot for AWS Bedrock Integration

This project implements a Slack bot that integrates with AWS Bedrock to provide AI capabilities directly in Slack. Built using AWS CDK with TypeScript, it deploys the required infrastructure to AWS.

Key features:
- Seamless integration with Slack's messaging and home tab interfaces
- Support for multiple AWS Bedrock models
- Customizable system prompts per model
- File handling capabilities including images and documents
- DynamoDB-backed user preferences storage

The infrastructure is defined as code using the AWS CDK, making it easy to deploy and maintain. The `cdk.json` file contains the configuration for the CDK Toolkit.

## Setup Instructions

1. AWS Account Setup
   - Create an AWS account if you don't have one
   - Create access keys for either the root user or create an admin IAM role and generate keys for it
   - Save these access keys for later use

2. Install Required Tools
   - Install the AWS CDK CLI: `npm install -g aws-cdk`
   - Install the AWS CLI: Follow instructions at https://aws.amazon.com/cli/
   
3. Configure AWS CLI
   - Run `aws configure` 
   - Enter your AWS access key ID and secret access key
   - Set default region (recommended: us-east-1)
   - Set output format (json is recommended)

4. Create Slack App
   - Go to https://api.slack.com/apps
   - Click "Create New App" -> "From an app manifest"
   - Select your workspace
   - Copy the YAML configuration from below this README
   - Replace the placeholders in angle brackets with your desired values
   - Create the app

5. Configure Slack App Events
   - In your Slack App settings, go to "Event Subscriptions"
   - Enable events and subscribe to:
     - app_home_opened
     - message.channels
     - message.im
     - message.groups

6. Create AWS Secret
   - Install the Slack app to your workspace to get the OAuth token
   - Get your signing secret from Basic Information in app settings
   - Create a new secret in AWS Secrets Manager using this command:
   ```bash
   aws secretsmanager create-secret \
   --name "slackllm" \
   --secret-string '{
       "SLACK_BOT_TOKEN": "xoxb-XXXXXXX-XXXXXXXXXXXXX-XXXXXXXXXXXXXXXXX",
       "SLACK_SIGNING_SECRET": "XXXXXXXXXXXXXXXXXXXXXXX"
   }'
   ```
   Replace the X's with your actual token and signing secret

7. Deploy the Application
   - Run `cdk deploy` in the project directory
   - Wait for deployment to complete
   - Note the Lambda function URL in the output

8. Complete Slack Configuration
   - Copy the Lambda function URL from the deployment output
   - In your Slack App settings:
     - Go to "Event Subscriptions"
     - Paste the URL in the "Request URL" field
     - Go to "Interactivity & Shortcuts"
     - Enable interactivity
     - Paste the same URL in the "Request URL" field
     - Save changes

Your SlackLLM bot should now be ready to use in your Slack workspace!


```
display_information:
  name: <whatever name you want>
  description: <whatever you want>
  background_color: "#05a88d"
features:
  app_home:
    home_tab_enabled: true
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
  bot_user:
    display_name: <whatever name you want>
    always_online: true
oauth_config:
  scopes:
    bot:
      - channels:history
      - chat:write
      - groups:history
      - im:history
      - im:read
      - im:write
      - files:read
settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

## Useful commands
* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
