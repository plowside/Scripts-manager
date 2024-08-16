#!/bin/bash
python -m uvicorn app.app:app --host 0.0.0.0 --port 80