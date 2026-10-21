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
- [x] Day 1: Project setup, proxy skeleton
- [x] Day 2: Reverse proxy forwarding
- [x] Day 3: Streaming + error handling
- [ ] DLP, Rules Engine, Classifier, Output Validator, Dashboard