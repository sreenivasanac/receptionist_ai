# AI Receptionist Backend

Keystone AI Receptionist - Backend API for self-care business chatbot.

## Setup

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the server
uv run python -m app.main
```

## API Endpoints

- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login
- `GET /business/{id}` - Get business details
- `PUT /business/{id}/config` - Update business config
- `POST /chat/message` - Send chat message
- `GET /chat/greeting/{business_id}` - Get greeting message
