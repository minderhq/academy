---
Document ID: 1100-QUIZ
Title: "1100: Network - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Beginner
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'networking', 'wan']
---

# 1100: Network - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. The OSI model has how many layers?**

A) 7
B) 3
C) 5
D) 10

**2. TCP is:**

A) Unreliable, the delivery guarantee UDP makes instead
B) Connection-oriented and reliable
C) Only for UDP
D) Connectionless

**3. DNS is used for:**

A) IP address allocation
B) Name resolution
C) Encryption
D) Routing

**4. A load balancer distributes:**

A) Network traffic across servers
B) Emails, a mail-server job that no balancer takes on
C) Storage
D) DNS queries

**5. Reverse proxy:**

A) Is not used
B) Forwards client requests to servers
C) Only for HTTP, a restriction reverse proxies never impose
D) Servers directly connect to clients

**6. HTTP typically runs on port:**

A) 22
B) 443
C) 80
D) 8080

**7. HTTPS uses:**

A) FTP, a file-transfer protocol with no role in HTTPS
B) No encryption
C) SSL/TLS encryption
D) SSH

**8. A CDN:**

A) Stores databases
B) Is not useful
C) Is only for video
D) Distributes content geographically

**9. Round-robin load balancing:**

A) Sends all to one server
B) Sends randomly
C) Rotates requests evenly
D) Is not used

**10. API rate limiting prevents:**

A) Fast responses, which rate limiting shapes but never exists to prevent
B) Abuse and overload
C) Authentication
D) Logging

**11. REST APIs use:**

A) HTTP methods (GET, POST, PUT, DELETE)
B) No methods, a design in which clients could never express intent
C) Only POST
D) Only GET

**12. JWT is used for:**

A) Database storage, a persistence role JWTs' signed claims do not fill
B) Load balancing
C) DNS
D) Authentication tokens

**13. Latency is:**

A) Bandwidth
B) Storage
C) Data transfer speed
D) Time delay

**14. Bandwidth is:**

A) Data transfer capacity
B) Server count
C) Time delay
D) Number of users, a head count no link-speed metric reports

**15. A VPC is:**

A) Virtual Private Cloud (isolated network)
B) Load balancer, a traffic-splitting component distinct from the isolated network
C) Public network
D) Database

**16. Security groups control:**

A) Database access
B) Network traffic rules
C) File permissions, an OS-level concern outside the security-group model
D) User passwords

**17. API gateway:**

A) Is a database
B) Not useful
C) Manages API requests
D) Is a load balancer only

**18. Circuit breaker pattern:**

A) Only for databases, a scope the pattern spans far beyond
B) Causes failures
C) Is not used
D) Prevents cascading failures

**19. Health checks:**

A) Only for load balancers
B) Are not useful
C) Monitor service status
D) Cause downtime

**20. Microservices communicate via:**

A) Files
B) Shared memory
C) Direct variable access, impossible across process boundaries in a distributed system
D) Network (APIs, message queues)

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | OSI has seven layers: Physical through Application |
| 2 | B | TCP handshakes and retransmits lost segments; UDP is the connectionless alternative |
| 3 | B | DNS resolves domain names to IP addresses |
| 4 | A | A load balancer spreads traffic across servers so no node is overwhelmed |
| 5 | B | A reverse proxy sits in front of servers and forwards client requests to them |
| 6 | C | 80 is HTTP's default port; 443 is HTTPS, 22 is SSH |
| 7 | C | HTTPS wraps HTTP in an SSL/TLS encrypted channel |
| 8 | D | A CDN caches content on geographically distributed edge nodes |
| 9 | C | Round-robin rotates requests through the server list in order |
| 10 | B | Rate limiting caps requests per client per window to stop abuse and overload |
| 11 | A | REST maps intent to HTTP verbs: GET/POST/PUT/DELETE |
| 12 | D | A JWT is a signed token carrying claims, used for authentication |
| 13 | D | Latency is time delay; bandwidth (capacity) is a different metric |
| 14 | A | Bandwidth is the data a link can carry per unit time |
| 15 | A | A VPC is a logically isolated private network in a cloud account |
| 16 | B | Security groups are allow/deny firewall rules for network traffic |
| 17 | C | An API gateway is the managed entry point for API requests |
| 18 | D | The breaker stops calls to a failing dependency so failures don't cascade |
| 19 | C | Health checks probe whether a service is up so traffic routes around failures |
| 20 | D | Separate processes talk over the network: REST/gRPC APIs or message queues |
