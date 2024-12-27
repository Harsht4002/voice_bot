from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .websocket import AIAgentWebSocket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_websocket = AIAgentWebSocket()

@app.websocket("/ws/agent/")
async def websocket_endpoint(websocket: WebSocket):
    await agent_websocket.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response = await agent_websocket.process_message(data)
            await websocket.send_text(response)
    except Exception as e:
        print(f"WebSocket error: {e}")