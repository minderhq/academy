---
Document ID: 2100-QUIZ
Title: "2100: Calculus - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'math', 'calculus']
---

# 2100: Calculus - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)
- **Time limit:** None

---

## Questions

**1. What is a derivative?**

A) The sum of values, an accumulation that integration rather than differentiation produces
B) The area under a curve
C) The rate of change of a function
D) The integral of a function

**2. The chain rule is used to:**

A) Find derivatives of composite functions
B) Find integrals, the reverse operation the chain rule never performs
C) Find derivatives of products
D) Find derivatives of quotients

**3. In backpropagation, we use:**

A) Both first and second derivatives
B) Neither
C) First derivatives only
D) Second derivatives only

**4. A gradient is:**

A) A single number, a description that fits the scalar, not the gradient
B) A matrix
C) A scalar
D) A vector of partial derivatives

**5. The learning rate in gradient descent is analogous to:**

A) The function value
B) The step size
C) The derivative
D) The gradient magnitude

**6. What does the second derivative tell us?**

A) The slope, a first-derivative reading that curvature does not repeat
B) The curvature (concavity)
C) The area
D) The intercept

**7. Partial derivatives are used when:**

A) A function has multiple variables
B) We want to find the maximum
C) A function has one variable
D) We want to integrate

**8. In neural networks, gradients flow:**

A) Forward only
B) Backward only
C) Neither direction
D) Both directions

**9. The gradient points in the direction of:**

A) Random direction
B) Steepest descent
C) Steepest ascent
D) No change

**10. To minimize a loss function, we move:**

A) Opposite to the gradient
B) Perpendicular to the gradient
C) In the direction of the gradient
D) Randomly

**11. The product rule is for:**

A) Quotients of functions
B) Products of functions
C) Sums of functions
D) Composite functions

**12. Local minima vs global minima:**

A) Local minima can be worse than global
B) Global minima don't exist
C) Local minima are always better, a ranking no loss landscape guarantees
D) Are always the same

**13. Saddle points:**

A) Are minima
B) Don't exist, a claim saddle points themselves refute in high dimensions
C) Are maxima
D) Are neither minima nor maxima

**14. The Hessian matrix contains:**

A) Function values, entries the Hessian never stores
B) Third derivatives
C) Second derivatives
D) First derivatives

**15. Convex functions have:**

A) Multiple local minima, a landscape feature convexity rules out
B) No minima
C) Infinite minima
D) Only one global minimum

**16. In optimization, "momentum" helps:**

A) Prevent learning, the opposite of what a momentum term is built for
B) Speed up and smooth convergence
C) Increase noise
D) Slow down convergence

**17. The Jacobian is:**

A) A matrix of second derivatives
B) A scalar
C) A vector
D) A matrix of first derivatives

**18. Gradient descent can get stuck in:**

A) Local minima or saddle points
B) Nowhere
C) Flat regions only, a claim that ignores minima and saddle points alike
D) Global minima

**19. Learning rate too high causes:**

A) Slow convergence
B) Better convergence, an outcome an oversized step rate never delivers
C) Divergence or oscillation
D) No effect

**20. A critical point occurs when:**

A) The learning rate is zero
B) The function is zero
C) The gradient is maximum
D) The gradient is zero

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-20:** [2102: Backpropagation and Automatic Differentiation](../2102-Backpropagation-and-Derivatives.md) — derivatives, gradients, and optimization

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | A derivative is the rate of change of a function - the instantaneous slope |
| 2 | A | The chain rule differentiates composite functions: outer function times inner derivative |
| 3 | C | Backpropagation propagates first derivatives (gradients) only |
| 4 | D | A gradient is the vector of all partial derivatives |
| 5 | B | The learning rate is the step size taken along the negative gradient |
| 6 | B | The second derivative measures curvature (concavity) |
| 7 | A | Partial derivatives apply when a function has multiple variables |
| 8 | B | Gradients flow backward through the network during the backward pass |
| 9 | C | The gradient points in the direction of steepest ascent |
| 10 | A | Gradient descent moves opposite to the gradient |
| 11 | B | The product rule differentiates products of functions |
| 12 | A | A local minimum can be worse than the global one |
| 13 | D | Saddle points are neither minima nor maxima |
| 14 | C | The Hessian is the matrix of second derivatives |
| 15 | D | Convexity guarantees a single global minimum |
| 16 | B | Momentum speeds up and smooths convergence |
| 17 | D | The Jacobian is the matrix of first partial derivatives |
| 18 | A | Plain gradient descent can stall in local minima or on saddle points |
| 19 | C | A too-high learning rate causes divergence or oscillation |
| 20 | D | A critical point is where the gradient vanishes |
