// University Front Door Support Agent - Azure Infrastructure
// Deploy with: azd provision

@description('Name prefix for all resources')
param resourcePrefix string = 'frontdoor'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Dedicated location for Cosmos DB when regional capacity is constrained')
param cosmosLocation string = 'canadacentral'

@description('Azure OpenAI deployment model')
param openAiModel string = 'gpt-4o'

@description('OpenAI model version')
param openAiModelVersion string = '2024-05-13'

@description('Enable mock mode (no external service connections)')
param mockMode bool = false

@description('Deployment timestamp for tagging')
param deploymentDate string = utcNow('yyyy-MM-dd')

// Naming convention
var resourceToken = toLower(uniqueString(subscription().id, resourceGroup().id, location))
var prefix = '${resourcePrefix}-${resourceToken}'
var keyVaultName = take(replace('${resourcePrefix}${resourceToken}kv', '-', ''), 24)
var cosmosToken = toLower(uniqueString(subscription().id, resourceGroup().id, cosmosLocation))
var cosmosAccountName = '${resourcePrefix}-${cosmosToken}-cosmos'

// Tags for all resources
var tags = {
  'azd-env-name': resourcePrefix
  'solution-accelerator': 'university-front-door-agent'
  'deployment-date': deploymentDate
}

// ============================================================================
// Azure OpenAI
// ============================================================================
resource openAi 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: '${prefix}-openai'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${prefix}-openai'
    publicNetworkAccess: 'Enabled'
  }
}

resource openAiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: openAiModel
  properties: {
    model: {
      format: 'OpenAI'
      name: openAiModel
      version: openAiModelVersion
    }
  }
  sku: {
    name: 'Standard'
    capacity: 30
  }
}

// ============================================================================
// Azure Cosmos DB
// ============================================================================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = if (!mockMode) {
  name: cosmosAccountName
  location: cosmosLocation
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    locations: [
      {
        locationName: cosmosLocation
        failoverPriority: 0
      }
    ]
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = if (!mockMode) {
  parent: cosmosAccount
  name: 'frontdoor'
  properties: {
    resource: {
      id: 'frontdoor'
    }
  }
}

resource sessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = if (!mockMode) {
  parent: cosmosDatabase
  name: 'sessions'
  properties: {
    resource: {
      id: 'sessions'
      partitionKey: {
        paths: [
          '/student_id_hash'
        ]
        kind: 'Hash'
      }
      defaultTtl: 7776000 // 90 days
    }
  }
}

resource auditContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = if (!mockMode) {
  parent: cosmosDatabase
  name: 'audit_logs'
  properties: {
    resource: {
      id: 'audit_logs'
      partitionKey: {
        paths: [
          '/timestamp'
        ]
        kind: 'Hash'
      }
    }
  }
}

// ============================================================================
// Azure AI Search
// ============================================================================
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${prefix}-search'
  location: location
  tags: tags
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

// ============================================================================
// Azure Container Apps Environment
// ============================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${prefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-08-01-preview' = {
  name: '${prefix}-env'
  location: location
  tags: tags
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

// ============================================================================
// Azure Key Vault
// ============================================================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enableRbacAuthorization: true
  }
}

// Store secrets
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-openai-api-key'
  properties: {
    value: openAi.listKeys().key1
  }
}

resource cosmosKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!mockMode) {
  parent: keyVault
  name: 'cosmos-db-key'
  properties: {
    value: cosmosAccount.listKeys().primaryMasterKey
  }
}

resource searchKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'search-api-key'
  properties: {
    value: searchService.listAdminKeys().primaryKey
  }
}

// ============================================================================
// Azure Container Registry
// ============================================================================
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: replace('${prefix}acr', '-', '')
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// ============================================================================
// Service Targets for azd deploy
// ============================================================================
resource backendContainerApp 'Microsoft.App/containerApps@2023-08-01-preview' = {
  name: '${prefix}-backend'
  location: location
  tags: union(tags, {
    'azd-service-name': 'backend'
  })
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        {
          name: 'acr-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            {
              name: 'MOCK_MODE'
              value: string(mockMode)
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

// ============================================================================
// Outputs for azd
// ============================================================================
output AZURE_OPENAI_ENDPOINT string = openAi.properties.endpoint
output AZURE_OPENAI_DEPLOYMENT string = openAiDeployment.name
output AZURE_COSMOS_ENDPOINT string = mockMode ? '' : cosmosAccount.properties.documentEndpoint
output AZURE_COSMOS_DATABASE string = mockMode ? 'frontdoor' : cosmosDatabase.name
output AZURE_SEARCH_ENDPOINT string = 'https://${searchService.name}.search.windows.net'
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output AZURE_CONTAINER_ENV_ID string = containerAppEnv.id
output AZURE_CONTAINERAPP_URL string = 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output AZURE_KEY_VAULT_NAME string = keyVault.name
output MOCK_MODE bool = mockMode
