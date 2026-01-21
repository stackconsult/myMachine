# CEP Machine - CopilotKit Integration

This repository contains the CEP (Customer Engagement Platform) Machine with CopilotKit integration for AI-powered business automation.

## Architecture

- **Frontend**: Next.js 14 with TypeScript, TailwindCSS, and CopilotKit
- **Backend**: FastAPI with Python, integrating 9 AI agent layers
- **Database**: Supabase (PostgreSQL)
- **Cache**: DragonflyDB (Redis-compatible)

## 9-Layer AI Agent Framework

1. **Prospect Research** - Finds businesses with weak GBP
2. **Pitch Generator** - Creates personalized outreach content
3. **Outreach Engine** - Multi-channel message delivery
4. **Booking Handler** - Calendly webhook to CRM integration
5. **Onboarding Flow** - Automated client setup
6. **GBP Optimizer** - Google Business Profile automation
7. **Reporting Engine** - Performance analytics with AI
8. **Finance Tracker** - Revenue and expense tracking
9. **Self-Learning** - Feedback loop for improvement

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Supabase account
- OpenAI API key (or Anthropic/Groq)

### 1. Clone and Install
```bash
git clone https://github.com/stackconsult/myMachine
cd myMachine
```

### 2. Environment Setup
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit .env with your API keys
nano .env
```

### 3. Start the Application
```bash
# Quick start (runs both frontend and backend)
./start-cep-machine.sh

# Or start manually:
# Terminal 1 - Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

### 4. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

## CopilotKit Integration

### Frontend Setup
The frontend uses CopilotKit React components:
- `CopilotKit` provider in `layout.tsx`
- `CopilotSidebar` for the main chat interface
- `CopilotChat` for layer-specific conversations

### Backend Setup
The backend integrates with CopilotKit via:
- FastAPI endpoint at `/api/copilotkit`
- 9 AI agents registered with the runtime
- Multi-model support (OpenAI, Anthropic, Groq)

### Agent Configuration
Each agent is defined in `backend/agents/` and can be:
- Local LangGraph agents
- CopilotKit Cloud agents (layers 1-3)
- Custom tools and actions

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (.env)
```
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Cache
DRAGONFLY_URL=redis://localhost:6379

# AI Models
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
MODEL_PROVIDER=openai

# CopilotKit (optional - for cloud agents)
COPILOTKIT_API_KEY=your_copilotkit_key
USE_CLOUD_AGENTS=true
```

## Usage

1. Open http://localhost:3000
2. Click the chat icon to open the CopilotKit sidebar
3. Interact with the AI assistant:
   - Ask about prospect research
   - Request pitch generation
   - Configure outreach campaigns
   - View analytics reports
4. Click on any layer to get specialized assistance

## Development

### Adding New Agents
1. Create agent in `backend/agents/new_agent.py`
2. Register in `backend/main.py`
3. Add UI component in frontend if needed

### Custom UI for Tools
Use CopilotKit's `useRenderToolCall` hook to render custom UI for agent tool calls.

### Multi-Tenant Support
Pass tenant context through CopilotKit properties:
```tsx
<CopilotKit properties={{ tenant_id: "123", user_type: "premium" }}>
```

## Deployment

### Docker
```bash
docker-compose up -d
```

### Production
- Frontend: Vercel/Netlify
- Backend: Railway/Render
- Database: Supabase
- Cache: Dragonfly Cloud

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test with `npm test` and `python -m pytest`
5. Submit PR

## License

MIT License - see LICENSE file
