/**
 * Module 5E: Universal Integration Hub - Basic Usage Examples
 * 
 * This file demonstrates basic usage patterns for the Universal Integration Hub.
 */

import {
  createUniversalIntegrationSystem,
  createUniversalAdapter,
  createProtocolTranslator,
  createDataTransformer,
  createAPIGateway,
  createIntegrationOrchestrator,
  IntegrationRequest,
  DiscoveryProtocol,
  ServiceProtocol,
  ProtocolType,
  DataFormat,
  HttpMethod
} from '../index';

/**
 * Example 1: Basic Integration System Setup
 */
async function example1_BasicSetup() {
  console.log('Example 1: Basic Integration System Setup\n');

  // Create integration system with default configuration
  const system = createUniversalIntegrationSystem();

  // Start the system
  await system.start();
  console.log('✅ Integration system started');

  // Get system statistics
  const stats = system.getStats();
  console.log('📊 System Stats:', {
    totalIntegrations: stats.totalIntegrations,
    activeIntegrations: stats.activeIntegrations,
    successRate: stats.successRate
  });

  // Stop the system
  await system.stop();
  console.log('✅ Integration system stopped\n');
}

/**
 * Example 2: Simple HTTP to gRPC Integration
 */
async function example2_SimpleIntegration() {
  console.log('Example 2: Simple HTTP to gRPC Integration\n');

  const system = createUniversalIntegrationSystem();
  await system.start();

  // Define integration request
  const request: IntegrationRequest = {
    id: 'http-to-grpc-1',
    source: {
      service: 'web-api',
      protocol: 'http',
      format: 'json'
    },
    target: {
      service: 'backend-service',
      protocol: 'grpc',
      format: 'protobuf'
    },
    data: {
      userId: 123,
      action: 'getUserProfile',
      timestamp: Date.now()
    },
    metadata: {
      priority: 'high',
      timeout: 5000
    }
  };

  // Execute integration
  const result = await system.integrate(request);

  console.log('📊 Integration Result:', {
    success: result.success,
    executionTime: `${result.executionTime}ms`,
    steps: result.steps.length
  });

  // Show execution steps
  result.steps.forEach((step, index) => {
    console.log(`  Step ${index + 1}: ${step.name} (${step.duration}ms) ${step.success ? '✅' : '❌'}`);
  });

  await system.stop();
  console.log();
}

/**
 * Example 3: Service Discovery with Universal Adapter
 */
async function example3_ServiceDiscovery() {
  console.log('Example 3: Service Discovery\n');

  // Create adapter with multiple discovery protocols
  const adapter = createUniversalAdapter({
    discovery: {
      protocols: [
        DiscoveryProtocol.DNS_SD,
        DiscoveryProtocol.MDNS,
        DiscoveryProtocol.CONSUL
      ],
      scanInterval: 60000,
      healthCheckInterval: 30000,
      timeout: 30000,
      maxConcurrent: 100,
      retryAttempts: 3,
      retryDelay: 1000
    },
    autoConnect: true
  });

  // Start discovery
  await adapter.startDiscovery();
  console.log('✅ Service discovery started');

  // Wait for services to be discovered
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Get discovered services
  const services = adapter.getAllServices();
  console.log(`📡 Discovered ${services.length} services`);

  // Search for specific services
  const httpServices = adapter.searchServices({
    protocol: ServiceProtocol.HTTP
  });
  console.log(`🔍 Found ${httpServices.length} HTTP services`);

  // Get discovery statistics
  const stats = adapter.getStats();
  console.log('📊 Discovery Stats:', {
    totalDiscovered: stats.totalDiscovered,
    totalConnected: stats.totalConnected,
    averageDiscoveryTime: `${stats.averageDiscoveryTime.toFixed(2)}ms`
  });

  await adapter.stopDiscovery();
  console.log('✅ Service discovery stopped\n');
}

/**
 * Example 4: Protocol Translation
 */
async function example4_ProtocolTranslation() {
  console.log('Example 4: Protocol Translation\n');

  const translator = createProtocolTranslator();

  // Create a message
  const message = {
    id: 'msg-1',
    sourceProtocol: ProtocolType.HTTP,
    targetProtocol: ProtocolType.GRPC,
    encoding: 'json' as any,
    headers: {
      'content-type': 'application/json',
      'authorization': 'Bearer token123'
    },
    body: {
      userId: 456,
      action: 'updateProfile',
      data: {
        name: 'John Doe',
        email: 'john@example.com'
      }
    },
    metadata: {},
    timestamp: new Date()
  };

  // Translate HTTP to gRPC
  const result = await translator.translate(message, ProtocolType.GRPC);

  console.log('📊 Translation Result:', {
    success: result.success,
    translationTime: `${result.translationTime}ms`,
    sourceSize: `${result.sourceSize} bytes`,
    targetSize: `${result.targetSize} bytes`
  });

  // Get translation statistics
  const stats = translator.getStats();
  console.log('📊 Translation Stats:', {
    totalTranslations: stats.totalTranslations,
    successRate: `${(stats.successfulTranslations / stats.totalTranslations * 100).toFixed(2)}%`,
    averageTime: `${stats.averageTranslationTime.toFixed(2)}ms`
  });

  console.log();
}

/**
 * Example 5: Data Transformation
 */
async function example5_DataTransformation() {
  console.log('Example 5: Data Transformation\n');

  const transformer = createDataTransformer();

  // Transform JSON to CSV
  const request = {
    id: 'transform-1',
    sourceFormat: DataFormat.JSON,
    targetFormat: DataFormat.CSV,
    data: [
      { id: 1, name: 'Alice', age: 30, city: 'New York' },
      { id: 2, name: 'Bob', age: 25, city: 'London' },
      { id: 3, name: 'Charlie', age: 35, city: 'Tokyo' }
    ],
    metadata: {}
  };

  const result = await transformer.transform(request);

  console.log('📊 Transformation Result:', {
    success: result.success,
    transformationTime: `${result.transformationTime}ms`,
    sourceSize: `${result.sourceSize} bytes`,
    targetSize: `${result.targetSize} bytes`
  });

  if (result.success && result.data) {
    console.log('📄 Transformed Data (CSV):');
    console.log(result.data);
  }

  console.log();
}

/**
 * Example 6: API Gateway Configuration
 */
async function example6_APIGateway() {
  console.log('Example 6: API Gateway Configuration\n');

  const gateway = createAPIGateway({
    port: 8080,
    host: '0.0.0.0',
    timeout: 30000,
    enableCors: true,
    enableCompression: true
  });

  // Register routes
  gateway.registerRoute({
    id: 'route-1',
    path: '/api/users/:id',
    method: HttpMethod.GET,
    target: 'http://backend:3000/users',
    timeout: 5000,
    retries: 3,
    rateLimit: {
      enabled: true,
      maxRequests: 100,
      windowMs: 60000
    },
    authentication: {
      enabled: true,
      type: 'jwt',
      options: {}
    },
    caching: {
      enabled: true,
      ttl: 300000
    },
    metadata: {}
  });

  console.log('✅ Route registered: GET /api/users/:id');

  // Start gateway
  await gateway.start();
  console.log('✅ API Gateway started on port 8080');

  // Get gateway statistics
  const stats = gateway.getStats();
  console.log('📊 Gateway Stats:', {
    totalRequests: stats.totalRequests,
    averageLatency: `${stats.averageLatency.toFixed(2)}ms`,
    throughput: `${stats.throughput.toFixed(2)} req/s`
  });

  await gateway.stop();
  console.log('✅ API Gateway stopped\n');
}

/**
 * Example 7: Workflow Orchestration
 */
async function example7_WorkflowOrchestration() {
  console.log('Example 7: Workflow Orchestration\n');

  const orchestrator = createIntegrationOrchestrator();

  // Define workflow
  const workflow = {
    id: 'user-registration-workflow',
    name: 'User Registration Workflow',
    description: 'Complete user registration process',
    version: '1.0.0',
    steps: [
      {
        id: 'validate-input',
        name: 'Validate Input',
        type: 'validate' as any,
        config: {
          validator: (data: any) => {
            return data.email && data.password;
          }
        },
        metadata: {}
      },
      {
        id: 'create-user',
        name: 'Create User',
        type: 'call_api' as any,
        config: {
          url: 'http://api/users',
          method: 'POST'
        },
        dependencies: ['validate-input'],
        metadata: {}
      },
      {
        id: 'send-email',
        name: 'Send Welcome Email',
        type: 'call_service' as any,
        config: {
          service: 'email-service',
          method: 'sendWelcome'
        },
        dependencies: ['create-user'],
        metadata: {}
      }
    ],
    metadata: {}
  };

  // Register workflow
  orchestrator.registerWorkflow(workflow);
  console.log('✅ Workflow registered:', workflow.name);

  // Execute workflow
  const result = await orchestrator.executeWorkflow(
    workflow.id,
    {
      email: 'user@example.com',
      password: 'secure123',
      name: 'New User'
    }
  );

  console.log('📊 Workflow Result:', {
    status: result.status,
    executionTime: `${result.executionTime}ms`,
    stepsCompleted: result.stepResults.size
  });

  console.log();
}

/**
 * Example 8: Complete Integration Pipeline
 */
async function example8_CompletePipeline() {
  console.log('Example 8: Complete Integration Pipeline\n');

  const system = createUniversalIntegrationSystem({
    enableAutoDiscovery: true,
    enableProtocolTranslation: true,
    enableDataTransformation: true,
    enableAPIGateway: true,
    enableOrchestration: true
  });

  await system.start();

  // Register workflow
  system.registerWorkflow({
    id: 'data-sync-workflow',
    name: 'Data Synchronization Workflow',
    description: 'Sync data between systems',
    version: '1.0.0',
    steps: [
      {
        id: 'fetch-data',
        name: 'Fetch Data',
        type: 'call_api' as any,
        config: {},
        metadata: {}
      },
      {
        id: 'transform-data',
        name: 'Transform Data',
        type: 'transform' as any,
        config: {},
        dependencies: ['fetch-data'],
        metadata: {}
      },
      {
        id: 'save-data',
        name: 'Save Data',
        type: 'call_api' as any,
        config: {},
        dependencies: ['transform-data'],
        metadata: {}
      }
    ],
    metadata: {}
  });

  // Execute integration with workflow
  const request: IntegrationRequest = {
    id: 'pipeline-1',
    source: {
      service: 'legacy-system',
      protocol: 'http',
      format: 'xml'
    },
    target: {
      service: 'modern-system',
      protocol: 'grpc',
      format: 'protobuf'
    },
    data: {
      records: [
        { id: 1, value: 'data1' },
        { id: 2, value: 'data2' }
      ]
    },
    workflow: 'data-sync-workflow',
    metadata: {
      batchSize: 100,
      priority: 'high'
    }
  };

  const result = await system.integrate(request);

  console.log('📊 Pipeline Result:', {
    success: result.success,
    executionTime: `${result.executionTime}ms`,
    steps: result.steps.map(s => ({
      name: s.name,
      component: s.component,
      duration: `${s.duration}ms`,
      success: s.success
    }))
  });

  // Get comprehensive statistics
  const stats = system.getStats();
  console.log('\n📊 System Statistics:');
  console.log('  Total Integrations:', stats.totalIntegrations);
  console.log('  Success Rate:', `${(stats.successRate * 100).toFixed(2)}%`);
  console.log('  Average Execution Time:', `${stats.averageExecutionTime.toFixed(2)}ms`);
  console.log('  Throughput:', `${stats.throughput.toFixed(2)} integrations/s`);

  await system.stop();
  console.log('\n✅ Pipeline completed\n');
}

/**
 * Run all examples
 */
async function runAllExamples() {
  console.log('='.repeat(80));
  console.log('Module 5E: Universal Integration Hub - Usage Examples');
  console.log('='.repeat(80));
  console.log();

  try {
    await example1_BasicSetup();
    await example2_SimpleIntegration();
    await example3_ServiceDiscovery();
    await example4_ProtocolTranslation();
    await example5_DataTransformation();
    await example6_APIGateway();
    await example7_WorkflowOrchestration();
    await example8_CompletePipeline();

    console.log('='.repeat(80));
    console.log('✅ All examples completed successfully!');
    console.log('='.repeat(80));
  } catch (error) {
    console.error('❌ Error running examples:', error);
  }
}

// Run examples if this file is executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}

export {
  example1_BasicSetup,
  example2_SimpleIntegration,
  example3_ServiceDiscovery,
  example4_ProtocolTranslation,
  example5_DataTransformation,
  example6_APIGateway,
  example7_WorkflowOrchestration,
  example8_CompletePipeline,
  runAllExamples
};