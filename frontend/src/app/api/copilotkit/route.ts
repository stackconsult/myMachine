import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  try {
    // Forward the request to the Python backend
    const response = await fetch(`${backendUrl}/api/copilotkit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: request.body,
    });
    
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('CopilotKit proxy error:', error);
    return new Response(JSON.stringify({ error: 'Failed to connect to backend' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function GET(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  try {
    // Forward the request to the Python backend
    const response = await fetch(`${backendUrl}/api/copilotkit`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('CopilotKit proxy error:', error);
    return new Response(JSON.stringify({ error: 'Failed to connect to backend' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
