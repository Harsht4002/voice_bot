import asyncio
from agent.ai_agent import AIAgent

class AIAgentWebSocket:
    def __init__(self):
        self.ai_agent = AIAgent()
        self.connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def disconnect(self, websocket):
        self.connections.remove(websocket)

    async def process_message(self, message):
        response = await asyncio.to_thread(self.ai_agent.process_input, message)
        return response