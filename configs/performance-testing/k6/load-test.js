// PROJECT-OMEGA Performance Testing with k6
// Load testing for LLM inference services

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const tokenThroughput = new Trend('token_throughput');
const requestLatency = new Trend('request_latency');
const ttft = new Trend('time_to_first_token'); // Time To First Token

// Test configuration
export const options = {
  stages: [
    // Ramp-up
    { duration: '1m', target: 5 },   // 5 users
    { duration: '1m', target: 10 },  // 10 users
    { duration: '2m', target: 20 },  // 20 users
    // Sustained load
    { duration: '5m', target: 20 },  // 20 users for 5 min
    // Ramp-down
    { duration: '1m', target: 5 },   // 5 users
    { duration: '1m', target: 0 },   // 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<5000'], // 95% of requests under 5s
    'http_req_failed': ['rate<0.05'],     // Error rate under 5%
    'errors': ['rate<0.05'],
    'request_latency': ['p(95)<4000'],
  },
};

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://192.168.1.50:8000';
const API_KEY = __ENV.API_KEY || '';

// Test prompts
const PROMPTS = [
  'Explain quantum computing in simple terms.',
  'What are the main differences between Python and JavaScript?',
  'Describe the process of photosynthesis.',
  'How does machine learning work?',
  'What is the meaning of life?',
];

// Random prompt selector
function getRandomPrompt() {
  return PROMPTS[Math.floor(Math.random() * PROMPTS.length)];
}

// vLLM completion test
export function vllmCompletion() {
  const prompt = getRandomPrompt();
  const payload = JSON.stringify({
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
    prompt: `<s>[INST] ${prompt} [/INST]`,
    max_tokens: 256,
    temperature: 0.7,
    stream: false,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    tags: { name: 'vLLM-Completion' },
  };

  const startTime = Date.now();
  const response = http.post(`${BASE_URL}/v1/completions`, payload, params);
  const endTime = Date.now();

  // Record metrics
  requestLatency.add(endTime - startTime);

  // Validate response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has text': (r) => r.json('choices.0.text') !== undefined,
    'response time < 10s': (r) => r.timings.duration < 10000,
  });

  errorRate.add(!success);

  // Calculate tokens per second
  if (success && response.json('usage')) {
    const tokensGenerated = response.json('usage.completion_tokens');
    const duration = (endTime - startTime) / 1000; // seconds
    const tps = tokensGenerated / duration;
    tokenThroughput.add(tps);
  }

  sleep(1);
}

// vLLM chat completion test
export function vllmChat() {
  const prompt = getRandomPrompt();
  const payload = JSON.stringify({
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
    messages: [
      { role: 'user', content: prompt }
    ],
    max_tokens: 256,
    temperature: 0.7,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    tags: { name: 'vLLM-Chat' },
  };

  const response = http.post(`${BASE_URL}/v1/chat/completions`, payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has message': (r) => r.json('choices.0.message.content') !== undefined,
  });

  errorRate.add(response.status !== 200);
  sleep(1);
}

// Streaming test
export function vllmStream() {
  const prompt = getRandomPrompt();
  const payload = JSON.stringify({
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
    prompt: `<s>[INST] ${prompt} [/INST]`,
    max_tokens: 128,
    temperature: 0.7,
    stream: true,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
    },
    tags: { name: 'vLLM-Stream' },
  };

  const startTime = Date.now();
  const response = http.post(`${BASE_URL}/v1/completions`, payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  // Time to first token estimation
  if (response.status === 200) {
    ttft.add(Date.now() - startTime);
  }

  sleep(0.5);
}

// ReAct Agent test
export function reactAgentTest() {
  const queries = [
    'What is 15% of 237?',
    'Search for information about quantum computing.',
    'Calculate the square root of 144.',
    'What is the capital of France?',
  ];

  const query = queries[Math.floor(Math.random() * queries.length)];
  const payload = JSON.stringify({
    query: query,
    max_iterations: 10,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: { name: 'ReAct-Agent' },
  };

  const response = http.post('http://192.168.1.50:8001/api/query', payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has answer': (r) => r.json('answer') !== undefined,
  });

  errorRate.add(response.status !== 200);
  sleep(2);
}

// GraphRAG test
export function graphragTest() {
  const queries = [
    'What is machine learning?',
    'Explain neural networks.',
    'What are the benefits of knowledge graphs?',
  ];

  const query = queries[Math.floor(Math.random() * queries.length)];
  const payload = JSON.stringify({
    query: query,
    top_k: 5,
    graph_depth: 2,
    alpha: 0.5,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: { name: 'GraphRAG' },
  };

  const response = http.post('http://192.168.1.50:8002/api/query', payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has context': (r) => r.json('context') !== undefined,
  });

  errorRate.add(response.status !== 200);
  sleep(1);
}

// Vector search test (Qdrant)
export function qdrantSearchTest() {
  const payload = JSON.stringify({
    vector: new Array(384).fill(0).map(() => Math.random()),
    limit: 10,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'api-key': __ENV.QDRANT_API_KEY || '',
    },
    tags: { name: 'Qdrant-Search' },
  };

  const response = http.post(
    `http://192.168.1.100:6334/collections/documents/points/search`,
    payload,
    params
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => Array.isArray(r.json('result')),
  });

  errorRate.add(response.status !== 200);
  sleep(0.1);
}

// Knowledge graph test (Neo4j)
export function neo4jQueryTest() {
  const payload = JSON.stringify({
    query: 'MATCH (n:Entity) RETURN count(n) as count',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${btoa('neo4j:' + (__ENV.NEO4J_PASSWORD || 'omega_change_me'))}`,
    },
    tags: { name: 'Neo4j-Query' },
  };

  const response = http.post('http://192.168.1.100:7474/db/neo4j/tx/commit', payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => r.json('results.0.data.0.row') !== undefined,
  });

  errorRate.add(response.status !== 200);
  sleep(0.1);
}

// Main test scenario
export default function () {
  // Run all tests in random order
  const tests = [
    vllmCompletion,
    vllmChat,
    reactAgentTest,
    graphragTest,
    qdrantSearchTest,
    neo4jQueryTest,
  ];

  const test = tests[Math.floor(Math.random() * tests.length)];
  test();
}

// Setup function
export function setup() {
  console.log(`Starting load test against ${BASE_URL}`);
  console.log(`Test stages: ${JSON.stringify(options.stages)}`);
}

// Teardown function
export function teardown(data) {
  console.log('Load test completed');
  console.log(`Error rate: ${errorRate.name}`);
  console.log(`Average token throughput: ${tokenThroughput.name}`);
}
