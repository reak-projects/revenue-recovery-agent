# Revenue Recovery Agent

An AI-powered revenue recovery system that helps businesses identify payment recovery opportunities, understand customer responses, track payment promises, and recommend appropriate recovery actions.

## 🚀 What It Does

The Revenue Recovery Agent combines Machine Learning, LLM-based customer message analysis, business rules, and persistent customer history to decide the most appropriate recovery action.

The system can:

- Predict the probability of payment recovery
- Understand customer payment-related messages
- Track payment promises
- Detect broken and fulfilled promises
- Handle partial and full payments
- Prevent duplicate payment processing
- Recommend recovery actions
- Escalate difficult cases
- Keep humans in the decision loop
- Store recovery history and audit events

---

## 🏗️ Architecture

```text
                    ┌─────────────────┐
                    │    Razorpay     │
                    │   Test Mode     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │ Persistent Data │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Customer /      │          │ Invoice /       │
     │ Payment History │          │ Payment State   │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              └──────────────┬─────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Machine Learning│
                    │ Recovery Score  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Gemini LLM      │
                    │ Message Analysis│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Policy / Safety │
                    │     Layer       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Recovery Action │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
          ┌───────────────┐     ┌────────────────┐
          │ Human Review  │     │ Audit Trail    │
          └───────────────┘     └────────────────┘
```

---

## ✨ Key Features

### Machine Learning

- Recovery probability prediction
- Customer payment-behavior analysis
- Payment success rate
- Reminder response behavior
- Promise history
- Payment delay behavior
- Dispute history
- Previous payment failures
- Persisted model predictions

### AI Customer Understanding

Gemini analyzes customer messages and identifies intents such as:

- `PAYMENT_PROMISE`
- `PAYMENT_ISSUE`
- `DISPUTE`
- `REQUEST_PAYMENT_LINK`
- `REFUSAL`
- `UNKNOWN`

It can also extract:

- Promised payment date
- Promised payment time
- Reminder strategy
- Reminder interval
- Confidence
- Reason for the recommendation

### Recovery Decision System

The system supports:

- `SEND_REMINDER`
- `SEND_PAYMENT_LINK`
- `TRACK_PROMISE`
- `ESCALATE`
- `CLOSE_CASE`

The LLM suggests a candidate strategy, while deterministic policy logic controls the final recovery action.

---

## 💳 Payment Recovery Flow

```text
Payment Failed
      ↓
Recovery Case Created
      ↓
Recovery Probability Predicted
      ↓
Customer Response Analysed
      ↓
Recovery Action
      ↓
Payment Promise?
   ┌──┴──┐
  Yes    No
   ↓      ↓
Track   Recovery
Promise  Strategy
   ↓
Promise Pending
   ↓
 ┌──────┴──────┐
 ↓             ↓
Paid       Deadline Passed
 ↓             ↓
Recovered   Promise Broken
 ↓             ↓
Close      New Recovery Action
```

---

## 🤝 Human-in-the-Loop

Important recovery decisions can be reviewed by a human.

Human reviewers can:

- Accept the AI recommendation
- Override the AI recommendation
- Provide a reason
- Store the review
- Preserve historical review decisions

This prevents the system from relying blindly on AI-generated decisions.

---

## 🧠 Customer Memory

The system maintains historical customer behavior including:

- Previous invoices
- Previous payments
- Late payments
- Unresolved invoices
- Payment delays
- Previous promises
- Promises kept
- Promises broken
- Reminder responses
- Previous payment failures
- Disputes

This history influences future recovery decisions.

---

## 🔄 Idempotency

The system contains protections against duplicate processing.

Examples:

- Duplicate payment processing is prevented using `payment_id`
- Duplicate failed-payment recovery cases are prevented
- Duplicate promises are detected
- Broken promises are evaluated only once
- Repeated recovered states do not create duplicate recovery actions
- Repeated identical customer messages are protected from duplicate processing
- Pending promise audit events are protected from duplicate creation

---

## 🗄️ Data Persistence

PostgreSQL stores:

- Customers
- Invoices
- Payments
- Recovery cases
- ML predictions
- Customer interactions
- Agent actions
- Human reviews
- Audit events

This allows the agent to maintain historical context instead of treating every recovery event as a completely new case.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| FastAPI | API layer |
| PostgreSQL | Persistent storage |
| Razorpay Test API | Payment/invoice integration |
| Google Gemini | Customer message analysis |
| LangGraph | Agent orchestration |
| Scikit-learn | Recovery prediction model |
| Pandas | Data processing |
| psycopg | PostgreSQL connection |
| Pydantic | Data validation |

---

## 📁 Project Structure

```text
revenue-recovery-agent/
│
├── app/
│   ├── agent/
│   │   ├── analyzer.py
│   │   ├── decision.py
│   │   └── orchestrator.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── customers.py
│   │   ├── invoices.py
│   │   ├── payments.py
│   │   ├── predictions.py
│   │   ├── actions.py
│   │   ├── interactions.py
│   │   ├── reviews.py
│   │   ├── audit.py
│   │   └── recovery.py
│   │
│   ├── integrations/
│   │   └── razorpay.py
│   │
│   ├── ml/
│   │   ├── features.py
│   │   └── predict.py
│   │
│   ├── recovery/
│   │   ├── promise.py
│   │   └── workflow.py
│   │
│   ├── services/
│   │   ├── customer_service.py
│   │   ├── invoice_service.py
│   │   └── recovery_service.py
│   │
│   └── models.py
│
├── data/
│   ├── recovery_dataset.csv
│   └── recovery_dataset_v2.csv
│
├── models/
│   ├── recovery_model.pkl
│   └── recovery_scaler.pkl
│
├── scripts/
│
├── main.py
├── sync_razorpay.py
├── generate_dataset.py
├── check_features.py
├── test_promise.py
├── test_promise_handler.py
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd revenue-recovery-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

#### macOS / Linux

```bash
source .venv/bin/activate
```

#### Windows

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file:

```env
DATABASE_URL=your_postgresql_connection_string

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

GEMINI_API_KEY=your_gemini_api_key
```

**Never commit `.env` to GitHub.**

---

## ▶️ Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Then open the FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 🤖 Machine Learning Model

The recovery model is a Logistic Regression classifier.

The model estimates the probability that an outstanding payment will be recovered based on customer and invoice behavior.

### Model Features

The model incorporates:

- Previous invoice history
- Payment success rate
- Late payment history
- Average payment delay
- Reminder response rate
- Reminder success rate
- Promise history
- Dispute history
- Payment failures
- Customer tenure
- Invoice amount
- Days overdue
- Previous outstanding amount

The trained model and scaler are stored under:

```text
models/
```

### Model Performance

The current model was evaluated using a stratified train/test split.

Key evaluation metrics:

- Accuracy: approximately `0.90`
- ROC-AUC: approximately `0.95`
- F1-score for recovery class: approximately `0.79`

These results are based on the project's synthetic recovery dataset and should not be interpreted as production performance.

---

## 🧩 Agent Decision Flow

The system separates AI reasoning from deterministic business decisions.

```text
Customer Message
       ↓
Gemini
       ↓
Intent + Candidate Action
       ↓
Recovery Probability
       ↓
Customer History
       ↓
Deterministic Policy
       ↓
Final Recovery Action
       ↓
Human Review (when required)
       ↓
Audit + Persistence
```

The LLM does not directly control financial operations.

---

## 🔐 Security

Sensitive credentials are stored through environment variables and excluded from version control.

The repository does not contain:

- Gemini API keys
- Razorpay secret keys
- Database credentials
- `.env` files

### Production Hardening

Razorpay webhook signature verification is a remaining production-hardening requirement.

The current implementation is intended as a functional/demo MVP using Razorpay Test Mode.

---

## ⚠️ Known Limitations

This project is a **demo-ready MVP**, not a production payment-recovery system.

Current limitations include:

- Razorpay webhook signature verification is not implemented.
- Concurrent webhook delivery is not fully race-safe.
- Razorpay integration currently uses Test Mode.
- ML artifacts were trained using an older scikit-learn version than the current runtime.
- Production-grade monitoring and deployment infrastructure are not included.

---

## 📊 Project Status

### Demo-ready MVP

Implemented capabilities include:

- ML-based recovery prediction
- AI customer-message analysis
- LangGraph orchestration
- Customer historical memory
- Payment promise lifecycle
- Partial payment handling
- Payment idempotency
- Duplicate recovery protection
- Human-in-the-loop review
- Persistent predictions
- Persistent audit trail
- Gemini failure handling
- Razorpay Test Mode integration

---

## 🎯 Design Philosophy

The system follows a controlled-agent architecture:

```text
LLM
 ↓
Understand customer message
 ↓
Suggest recovery strategy
 ↓
Deterministic policy validates strategy
 ↓
Recovery action
 ↓
Human review when required
 ↓
Persist outcome + audit event
```

This separation keeps AI reasoning independent from sensitive financial operations and makes the system easier to test and eventually harden for production.

---

## 🧪 Testing

The project includes focused tests for:

- Payment promise lifecycle
- Duplicate promises
- New promises
- Pending promises
- Broken promises
- Recovered promises
- Partial payments
- Full payments
- Payment replay/idempotency
- Duplicate recovery prevention
- ML feature ordering
- Prediction persistence
- Gemini failure handling
- Human review behavior
- Audit persistence

---

## 🔮 Future Improvements

Potential production improvements include:

- Razorpay webhook signature verification
- Stronger concurrent webhook protection
- Production-grade message delivery
- Automated reminder scheduling
- Better model monitoring
- Real-world labelled recovery data
- Model retraining pipeline
- Production observability
- Role-based access control
- Deployment and CI/CD

---

## 👤 Author

**Regency Patel**

Built as an AI/ML engineering project focused on intelligent revenue recovery, payment workflows, agent orchestration, customer memory, and human-in-the-loop decision systems.