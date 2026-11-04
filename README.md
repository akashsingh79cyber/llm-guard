# LLM-Guard: Generative AI Prompt Firewall

Reverse proxy jo LLM ke saamne baith kar prompt injection, jailbreak
aur data leak rokta hai.

![Architecture](docs/architecture.png)

## Setup
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```
uvicorn tests.mock_llm:app --port 9000      # mock LLM
uvicorn app.main:app --reload --port 8000   # LLM-Guard proxy
```

## Status
- ## Status
- [x] Project setup, proxy skeleton
- [x] Reverse proxy forwarding
- [x] Streaming + error handling
- [x] DLP engine (mask/unmask)
- [x] Rules Engine (length limit, keyword block)
- [x] Safe system instructions
- [x] Jailbreak classifier, Output Validator, RBAC, Dashboard
- [x] Jailbreak dataset (collect + clean)
- [x] Baseline classifier (TF-IDF + LogReg)
- [x] Better classifier (word + char n-gram SVM) + model comparison
- [x] Threshold tuning + evaluation report
- [x] ML classifier integrated in proxy (live jailbreak block)
- [x] Telemetry logging (JSON, SIEM format)
- [x] Output validation (PII/secret leak redaction)
- [x] Model retrain + obfuscation normalization (red team tuning)
- [x] Toxic content output filter
- [x] RBAC: JWT login and token verification