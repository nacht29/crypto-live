# Timeframe: 10–12 Weeks (6–7 hours/week)

Goal:
Build a **credible, end-to-end time-series prediction model** (Bitcoin prices) using
statistical learning, scikit-learn, and AWS SageMaker — with **only the math that is
actually necessary**, learned just-in-time.

---

## Main Topic 0: Math Prerequisites (Foundational, Weeks 0–1, parallel)

### Summary & Purpose
Establish *just enough* math literacy so later ML concepts feel intuitive instead of
magical. This is **not** a full math course — it is a survival kit.

### Primary Resource (invest here)
- **Practical Statistics for Data Scientists** (selected chapters only)

### Subtopics

### 0.1 Descriptive Statistics
- Mean, median, variance, standard deviation
- Percentiles
- Outliers

**Materials**

- [Practical Statistics for Data Scientists](https://datapot.vn/wp-content/uploads/2023/12/datapot.vn-Practical-Statistics-for-Data-Scientists.pdf):
  - [Chapter 1](https://datapot.vn/wp-content/uploads/2023/12/datapot.vn-Practical-Statistics-for-Data-Scientists.pdf#%5B%7B%22num%22%3A125%2C%22gen%22%3A0%7D%2C%7B%22name%22%3A%22XYZ%22%7D%2Cnull%2C589.5%2Cnull%5D) 

**Hands-on**
- Code examples from the textbook
- Compute mean, std, percentiles on Bitcoin price data
- Plot price distribution

(Data: your crypto-live Bitcoin data from S3 or a local CSV extract)

---

### 0.2 Probability Intuition (Non-formal)
- Random variables
- Noise vs signal
- Expectation (conceptual, not proofs)

**Materials**
- Practical Statistics for Data Scientists:
  - Probability & distributions (skim)
- StatQuest:
  - “Probability Basics”

**Hands-on**
- Simulate noisy price series
- Observe how averages stabilize noise

(Data: synthetic data generated in code)

---

### 0.3 Linear Algebra (Minimal)
- Vectors as lists of numbers
- Dot product as weighted sum
- Matrices as tables (no operations)

**Materials**
- Khan Academy:
  - Vectors & dot product (conceptual videos only)
- StatQuest:
  - “Linear Algebra for Machine Learning” (overview)

**Hands-on**
- Manually compute a dot product
- Relate it to a regression prediction

(Data: small synthetic vectors)

---

## Main Topic 1: Statistical Learning Fundamentals (Weeks 1–2)

### Prerequisite Math
- Mean, variance
- Concept of randomness
- Vectors as feature lists

### Summary & Purpose
Build the correct **mental model** for ML:
- What statistical learning optimizes for
- Why prediction ≠ explanation
- How models generalize

### Primary Resource (invest here)
- **An Introduction to Statistical Learning (ISL)**

### Subtopics

### 1.1 What Is Statistical Learning?
- Prediction vs inference
- Supervised learning
- Training vs test error

**Materials**
- ISL Chapters 1–2
- ISL Lecture Videos (Ch 1–2)

**Hands-on**
- No coding
- Write a short note explaining:
  - What is being predicted?
  - What counts as success?

---

### 1.2 End-to-End ML Workflow
- Data → features → model → evaluation
- Overfitting intuition

**Materials**
- ISL Chapter 2 (end-to-end examples)

**Hands-on**
- Sketch ML workflow for Bitcoin prediction

---

## Main Topic 2: Regression Models (Weeks 3–4)

### Prerequisite Math
- Weighted sums (dot product)
- Squared differences
- Averages

### Summary & Purpose
Learn **core predictive models** that form strong baselines in real-world ML.

### Primary Resource (invest here)
- **ISL Chapter 3 + selected Chapter 6**

### Subtopics

### 2.1 Linear Regression
- Coefficients as weights
- Loss functions (MSE, MAE)

**Materials**
- ISL Chapter 3
- ISL Lecture Video (Linear Regression)

**Hands-on**
- ISL lab:
  - Train Linear Regression
  - Compare train vs test error

(Data: ISL datasets or synthetic data)

---

### 2.2 Regularization (Ridge & Lasso)
- Overfitting control
- Bias–variance tradeoff

**Materials**
- ISL Chapter 6 (Ridge/Lasso sections)

**Hands-on**
- Extend regression:
  - Ridge vs Lasso
  - Observe coefficient shrinkage

(Data: same dataset)

---

## Main Topic 3: Model Evaluation & Validation (Weeks 5–6)

### Prerequisite Math
- Mean & absolute difference
- Variance intuition
- Sampling concept

### Summary & Purpose
Learn how to **evaluate models honestly** and avoid self-deception.

### Primary Resource (invest here)
- **ISL Chapter 5**

### Subtopics

### 3.1 Train/Test Split & Cross-Validation
- Generalization error
- Validation logic

**Materials**
- ISL Chapter 5
- ISL Lecture Video (Resampling)

**Hands-on**
- Train/test split experiments
- Compare multiple splits

(Data: ISL datasets or synthetic)

---

### 3.2 Regression Metrics
- MAE vs RMSE
- Why R² can mislead

**Materials**
- ISL Chapter 5 (metrics discussion)

**Hands-on**
- Evaluate one model using multiple metrics
- Write a brief metric comparison note

---

## Main Topic 4: Time-Series Modeling (Weeks 7–8)

### Prerequisite Math
- Moving averages
- Variance over time
- Differences between values

### Summary & Purpose
Adapt statistical learning to **temporal data** without leakage.

### Primary Resource (invest here)
- **ISL + your own data**

### Subtopics

### 4.1 Time-Series Structure & Baselines
- Temporal ordering
- Naive forecasts

**Materials**
- ISL time-series examples
- Forecasting: Principles and Practice (selected sections)

**Hands-on**
- Baseline:
  - Predict next price = last price
- Evaluate baseline MAE

(Data: Bitcoin Parquet data from S3)

---

### 4.2 Feature Engineering for Time-Series
- Lag features
- Rolling statistics
- Returns

**Materials**
- ISL conceptual guidance
- scikit-learn docs (feature patterns)

**Hands-on Mini-Project**
- Build feature table:
  - price(t-1), price(t-5), price(t-60)
  - rolling mean & std
- Train Linear Regression
- Compare to baseline

(Data: your crypto-live Bitcoin dataset)

---

## Main Topic 5: Tree-Based Models (Weeks 9–10)

### Prerequisite Math
- Comparisons (<, >)
- Averages
- Concept of partitions

### Summary & Purpose
Introduce **non-linear models** with minimal extra math.

### Primary Resource (invest here)
- **ISL Chapter 8**

### Subtopics

### 5.1 Decision Trees & Random Forests
- Recursive splitting
- Feature importance

**Materials**
- ISL Chapter 8
- ISL Lecture Video (Trees)

**Hands-on**
- Train RandomForestRegressor
- Compare MAE vs Linear Regression
- Inspect feature importance

(Data: Bitcoin feature dataset)

---

## Main Topic 6: AWS SageMaker Integration (Weeks 11–12)

### Prerequisite Math
- None new (focus is engineering)

### Summary & Purpose
Convert models into a **cloud ML pipeline** suitable for production and portfolio review.

### Primary Resource (invest here)
- **AWS SageMaker official sklearn examples**

### Subtopics

### 6.1 SageMaker Training Jobs
- Training scripts
- S3 input/output
- Model artifacts

**Materials**
- SageMaker docs: “Train a Model with Scikit-Learn”
- Official example notebooks

**Hands-on Mini-Project**
- Convert notebook to `train.py`
- Upload data to S3
- Run SageMaker training job
- Save model artifact

(Data: S3-hosted Bitcoin dataset)

---

### 6.2 Batch Inference (Optional)
- Offline prediction
- Cost-efficient inference

**Materials**
- SageMaker Batch Transform docs

**Hands-on**
- Run batch inference
- Store predictions back to S3

---

## Final Outcome

You will finish with:
- Just-in-time math understanding
- Solid statistical learning intuition
- Correct time-series modeling practice
- A full AWS SageMaker ML pipeline
- A portfolio project that signals **applied ML competence**, not theoretical posturing
