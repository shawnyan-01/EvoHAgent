from client_server.game_agent_server import GameServerAgent
import asyncio
if __name__ == "__main__":
    
    server = GameServerAgent(host="0.0.0.0", port=9495)
    asyncio.run(server.start())

