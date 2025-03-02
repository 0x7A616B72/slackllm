import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';
import { Construct } from 'constructs';

export class SlackllmStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Parameters
    const slackSecretsName = new cdk.CfnParameter(this, 'SlackSecretsName', {
      type: 'String',
      default: 'slackllm'
    });

    const memorySize = new cdk.CfnParameter(this, 'MemorySize', {
      type: 'Number',
      default: 512,
      minValue: 128,
      maxValue: 2048,
    });

    // DynamoDB Table
    const table = new dynamodb.Table(this, 'SlackllmTable', {
      tableName: 'Slackllm',
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const lambdaRole = new iam.Role(this, 'SlackllmRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      sid: 'AllowBedrockInvoke',
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: ['*']
    }));

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      sid: 'AllowLambdaSelfInvoke',
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [`arn:aws:lambda:${this.region}:${this.account}:function:Slackllm`]
    }));

    const lambdaFn = new lambda.Function(this, 'Slackllm', {
      functionName: 'Slackllm',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'slackllm.lambda_handler',
      role: lambdaRole,
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      memorySize: memorySize.valueAsNumber,
      timeout: cdk.Duration.minutes(5),
      reservedConcurrentExecutions: 10,
      environment: {
        SLACK_BOT_TOKEN: `{{resolve:secretsmanager:${slackSecretsName.valueAsString}:SecretString:SLACK_BOT_TOKEN}}`,
        SLACK_SIGNING_SECRET: `{{resolve:secretsmanager:${slackSecretsName.valueAsString}:SecretString:SLACK_SIGNING_SECRET}}`,
        BEDROCK_MODEL_ID: 'arn:aws:bedrock:us-east-1:705478596818:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        DYNAMODB_TABLE_NAME: table.tableName
      }
    });

    table.grantReadWriteData(lambdaRole);

    const fnUrl = lambdaFn.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE
    });

    new cdk.CfnOutput(this, 'SlackllmUrl', {
      value: fnUrl.url
    });
  }
}