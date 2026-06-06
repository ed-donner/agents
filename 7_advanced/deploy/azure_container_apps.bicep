// Azure Container Apps deployment for the enterprise agent.
// Usage:
//   az login
//   az group create --name enterprise-agent-rg --location eastus
//   az deployment group create \
//     --resource-group enterprise-agent-rg \
//     --template-file azure_container_apps.bicep \
//     --parameters openaiApiKey=sk-...

@description('Container image to deploy (must be in ACR or Docker Hub)')
param containerImage string = 'YOUR_ACR.azurecr.io/enterprise-agent:latest'

@description('OpenAI API key')
@secure()
param openaiApiKey string

@description('Max spend in USD for the global budget')
param globalBudgetUsd string = '50.0'

@description('Max spend per user in USD')
param perUserBudgetUsd string = '2.0'

param location string = resourceGroup().location
param environmentName string = 'enterprise-agent-env'
param appName string = 'enterprise-agent'


// Log Analytics workspace for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${appName}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}


// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}


// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['POST', 'GET']
        }
      }
      secrets: [
        { name: 'openai-api-key', value: openaiApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'OPENAI_API_KEY', secretRef: 'openai-api-key' }
            { name: 'GLOBAL_BUDGET_USD', value: globalBudgetUsd }
            { name: 'PER_USER_BUDGET_USD', value: perUserBudgetUsd }
            { name: 'AUDIT_LOG_FILE', value: '' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 3
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0    // scale to zero when idle
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: { metadata: { concurrentRequests: '50' } }
          }
        ]
      }
    }
  }
}


output agentUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
