# LLM-Guard: Generative AI Prompt Firewall

Reverse proxy jo enterprise LLM ke saamne baith kar prompt injection, jailbreak aur data leakage rokta hai.

![Architecture](docs/architecture.png)

## Features
- JWT login aur role-based access (admin / employee / guest)
- Rules engine (role-based length limit, blocked phrases)
- ML jailbreak classifier (word + char n-gram SVM) with obfuscation normalization
- DLP engine: mask and unmask PII (email, card, SSN, Aadhaar, PAN, API key)
- Output validator: PII leak redaction, toxic filter, system prompt leak block (streaming bhi)
- JSON telemetry logs (SIEM ready)
- Streamlit SOC dashboard
- Red team simulator and system test suite

## Setup
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
`.env.example` ko `.env` me copy karke values bharo.

## Run
```
uvicorn tests.mock_llm:app --port 9000      # mock LLM
uvicorn app.main:app --port 8000            # LLM-Guard proxy
streamlit run dashboard/app.py --server.port 8501   # dashboard
```

## Test
```
python scripts/red_team.py
python scripts/system_test.py
python scripts/latency_audit.py
python scripts/final_metrics.py
```

## Results
Red team block rate: [70]% | False block: [50]% | Guard overhead: [50] ms | System tests: [20]/19

## Docs
- Final report: `report/FINAL_REPORT.md`
- Daily proof: `docs/Proof_Screenshots`