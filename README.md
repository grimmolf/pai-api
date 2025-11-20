# Bob API

The communication backbone for the Bob <-> Patterson AI Bridge.

## Overview
This repository contains the source code for the FastAPI-based communication node that allows Bob (local PAI) to talk to Patterson (remote PAI).

## Getting Started

### Prerequisites
- Python 3.11+
- Access to the local network

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### Running
```bash
uvicorn main:app --reload
```

