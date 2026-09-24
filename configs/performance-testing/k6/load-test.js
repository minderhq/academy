// ai-engineering-curriculum Performance Testing with k6
// Load testing for LLM inference services (vLLM + Qdrant + Neo4j)
//
// Usage:
//   k6 run -e BASE_URL=http://localhost:8000 load-test.js
//   k6 run -e BASE_URL=http://localhost:8000 -e SCENARIO=chat load-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

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

// Configuration (all overridable via environment)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || '';
const MODEL = __ENV.MODEL || 'Qwen/Qwen2.5-7B-Instruct-AWQ';
const QDRANT_URL = __ENV.QDRANT_URL || 'http://localhost:6333';
const NEO4J_URL = __ENV.NEO4J_URL || 'http://localhost:7474';

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

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
  };
}

// vLLM completion test
export function vllmCompletion() {
  const prompt = getRandomPrompt();
  const payload = JSON.stringify({
    model: MODEL,
    prompt: prompt,
    max_tokens: 256,
    temperature: 0.7,
    stream: false,
  });

  const params = { headers: authHeaders(), tags: { name: 'vLLM-Completion' } };

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
    model: MODEL,
    messages: [
      { role: 'user', content: prompt }
    ],
    max_tokens: 256,
    temperature: 0.7,
  });

  const params = { headers: authHeaders(), tags: { name: 'vLLM-Chat' } };

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
    model: MODEL,
    prompt: prompt,
    max_tokens: 128,
    temperature: 0.7,
    stream: true,
  });

  const params = { headers: authHeaders(), tags: { name: 'vLLM-Stream' } };

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

// Vector search test (Qdrant REST API, default port 6333)
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
    `${QDRANT_URL}/collections/documents/points/search`,
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

// Knowledge graph test (Neo4j HTTP transactional endpoint)
export function neo4jQueryTest() {
  const payload = JSON.stringify({
    statements: [
      { statement: 'MATCH (n) RETURN count(n) as count' },
    ],
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${btoa('neo4j:' + (__ENV.NEO4J_PASSWORD || 'changeme'))}`,
    },
    tags: { name: 'Neo4j-Query' },
  };

  const response = http.post(`${NEO4J_URL}/db/neo4j/tx/commit`, payload, params);

  check(response, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => r.json('results.0.data.0.row') !== undefined,
  });

  errorRate.add(response.status !== 200);
  sleep(0.1);
}

// Main test scenario — set SCENARIO=chat|completion|stream|qdrant|neo4j to
// run a single test type; default mixes all of them at random.
export default function () {
  const scenario = __ENV.SCENARIO || '';
  const tests = {
    'completion': vllmCompletion,
    'chat': vllmChat,
    'stream': vllmStream,
    'qdrant': qdrantSearchTest,
    'neo4j': neo4jQueryTest,
  };

  const test = tests[scenario] ||
    [vllmCompletion, vllmChat, qdrantSearchTest][Math.floor(Math.random() * 3)];
  test();
}

// Setup function
export function setup() {
  console.log(`Starting load test against ${BASE_URL} (model: ${MODEL})`);
  console.log(`Test stages: ${JSON.stringify(options.stages)}`);
}

// Teardown function
export function teardown(data) {
  console.log('Load test completed');
}
