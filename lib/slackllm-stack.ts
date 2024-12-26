import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';

export class SlackllmStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
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
      maxValue: 10240
    });

    // DynamoDB Table
    const table = new dynamodb.Table(this, 'SlackllmTable', {
      tableName: 'Slackllm',
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN
    });

    // Lambda Function
    const lambdaFn = new lambda.Function(this, 'Slackllm', {
      functionName: 'Slackllm',
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      handler: 'slackllm.lambda_handler',
      code: lambda.Code.fromAsset('./src'),
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

    // Function URL
    const fnUrl = lambdaFn.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE
    });

    // IAM Policies
    lambdaFn.addToRolePolicy(new iam.PolicyStatement({
      sid: 'AllowLambdaSelfInvoke', 
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [`${lambdaFn.functionArn}*`]
    }));

    lambdaFn.addToRolePolicy(new iam.PolicyStatement({
      sid: 'AllowBedrockInvoke',
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel'],
      resources: ['*']
    }));

    table.grantReadWriteData(lambdaFn);

    // Outputs
    new cdk.CfnOutput(this, 'SlackllmUrl', {
      value: fnUrl.url
    });
  }
}