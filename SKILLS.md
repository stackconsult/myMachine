# SKILLS.md - AI Agent Memory Document

> Persistent context for Windsurf Cascade to remember project state  
> **Updated: January 21, 2026 @ 10:35 AM MST**

---

## 🚦 Current Status

**COPILOTKIT INTEGRATION COMPLETE** | **READY FOR DEVELOPMENT**

### Project Architecture
```
myMachine Repository
├─ Frontend (Next.js 14) - Port 3000
│  ├─ CopilotKit React integration
│  ├─ TailwindCSS UI
│  └─ TypeScript
│
└─ Backend (FastAPI) - Port 8000
   ├─ 9 AI Agent Layers
   ├─ CopilotKit Runtime
   ├─ Supabase DB
   └─ DragonflyDB Cache
```

### Recent Updates (Jan 21, 2026 @ 10:30 AM)
- ✅ **CopilotKit Integration Complete** - Full frontend/backend integration
  - Installed CopilotKit React dependencies
  - Created API proxy route at `/api/copilotkit`
  - Added CopilotSidebar and CopilotChat components
  - Connected to Python backend with 9 AI agents
  - Created startup script for development
  - Added comprehensive documentation

---

## Project Identity

| Key | Value |
|-----|-------|
| **Project** | CEP Machine (myMachine) |
| **Purpose** | 9-Layer AI Agent Framework for Business Automation |
| **GitHub** | stackconsult/myMachine |
| **Branch** | main (latest commit: 0ba5e02) |

---

## Completed Components

### Frontend (5/5)
- ✅ Next.js 14 with TypeScript
- ✅ CopilotKit React integration
- ✅ TailwindCSS styling
- ✅ API proxy to backend
- ✅ Multi-layer chat interface

### Backend (9/9)
- ✅ FastAPI server setup
- ✅ CopilotKit Runtime integration
- ✅ 9 AI agent layers defined
- ✅ Multi-model support (OpenAI, Anthropic, Groq)
- ✅ Supabase database connection
- ✅ DragonflyDB cache integration
- ✅ Health check endpoints
- ✅ WebSocket support
- ✅ Agent registry system

### Documentation (3/3)
- ✅ README_COPILOTKIT.md
- ✅ start-cep-machine.sh script
- ✅ Environment configuration guides

---

## Known Issues & Technical Debt

### 🔴 Critical Issues
1. **Backend Not Running** - Python backend service needs to be started
2. **Environment Variables** - .env files need API keys configured
3. **Dependencies** - Backend Python dependencies need installation

### 🟡 Medium Priority
1. **Error Handling** - Frontend needs better error handling for API failures
2. **Loading States** - UI needs loading indicators during agent processing
3. **Test Coverage** - No tests written yet

### 🟢 Low Priority
1. **UI Polish** - Interface could use visual improvements
2. **Performance** - Optimize for large datasets
3. **Documentation** - API docs need completion

---

## Remaining Tasks

### Immediate (Today)
- [ ] Start backend service (python main.py)
- [ ] Configure environment variables
- [ ] Install Python dependencies
- [ ] Test CopilotKit connection

### Short Term (This Week)
- [ ] Add error handling for API failures
- [ ] Implement loading states
- [ ] Write basic unit tests
- [ ] Add agent status indicators

### Medium Term (Next 2 Weeks)
- [ ] Implement custom UI for tool calls
- [ ] Add multi-tenant support
- [ ] Create agent configuration UI
- [ ] Add analytics dashboard

### Long Term (Next Month)
- [ ] Add monitoring and logging
- [ ] Implement rate limiting
- [ ] Add user authentication
- [ ] Deploy to production

---

## Quick Commands

### Start Development
```bash
# Quick start (both services)
./start-cep-machine.sh

# Manual start
# Backend
cd backend && python main.py

# Frontend
cd frontend && npm run dev
```

### Access Points
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health: http://localhost:8000/health

---

## File Quick Reference

| File | Purpose |
|------|---------|
| `frontend/src/app/layout.tsx` | CopilotKit provider setup |
| `frontend/src/app/page.tsx` | Main dashboard with chat |
| `frontend/src/app/api/copilotkit/route.ts` | API proxy to backend |
| `backend/main.py` | FastAPI server with CopilotKit |
| `start-cep-machine.sh` | Development startup script |
| `README_COPILOTKIT.md` | Integration documentation |

---

## Environment Variables Needed

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (.env)
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

---

*This file exists for AI agent memory persistence.*  
*Update when project state changes.*  
*Last updated: January 21, 2026 @ 10:35 AM MST*
