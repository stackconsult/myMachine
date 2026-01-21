#!/bin/bash
# CEP Machine with CopilotKit Integration Startup Script

echo "🚀 Starting CEP Machine with CopilotKit Integration..."

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env not found. Copying .env.example..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your API keys"
fi

# Start DragonflyDB
echo "🐲 Starting DragonflyDB cache..."
docker-compose up -d dragonfly
if [ $? -eq 0 ]; then
    echo "✅ DragonflyDB started on port 6379"
else
    echo "❌ Failed to start DragonflyDB"
    exit 1
fi

# Wait for DragonflyDB to be ready
echo "⏳ Waiting for DragonflyDB to be ready..."
sleep 5

# Check DragonflyDB connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ DragonflyDB is ready"
else
    echo "❌ DragonflyDB not responding"
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "✅ CEP Machine is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to kill both processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    
    # Stop DragonflyDB
    echo "🐲 Stopping DragonflyDB..."
    docker-compose down
    
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait
