# example radicale-mcp bridge server
# reads radicale auth info from .env
# deps: pip install websockets caldav asyncio python-dotenv
# use mcp_client_test.py for testing
# see mcp-radicale.service for installation

import json
import asyncio
import websockets
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp-radicale-bridge")

from dotenv import load_dotenv
from radicale_calendar_manager import RadicaleCalendarManager

# Load environment variables from .env file
load_dotenv()

# Radicale connection settings from .env file
RADICALE_URL = os.getenv("RADICALE_URL", "http://localhost:5232")
RADICALE_USERNAME = os.getenv("RADICALE_USERNAME", "")
RADICALE_PASSWORD = os.getenv("RADICALE_PASSWORD", "")

# MCP Server settings
MCP_HOST = "localhost"
MCP_PORT = 8765

class MCPRadicaleBridge:
    def __init__(self):
        self.calendar_manager = RadicaleCalendarManager(
            url=RADICALE_URL,
            username=RADICALE_USERNAME,
            password=RADICALE_PASSWORD
        )

    async def connect(self):
        """Establish connection to Radicale server"""
        try:
            success = self.calendar_manager.connect()
            if not success:
                logger.warning("Failed to connect to Radicale or no calendars found")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Radicale: {e}")
            return False

    async def handle_mcp_request(self, message):
        """Process an incoming MCP request"""
        try:
            data = json.loads(message)

            # Handle different MCP request types
            if data.get("type") == "query":
                return await self.handle_query(data)
            elif data.get("type") == "create":
                return await self.handle_create(data)
            elif data.get("type") == "update":
                return await self.handle_update(data)
            elif data.get("type") == "delete":
                return await self.handle_delete(data)
            else:
                return {"status": "error", "message": "Unknown request type"}

        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON"}
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_query(self, data):
        """Handle query requests"""
        try:
            calendar_name = data.get("calendar", None)
            start_date = data.get("start_date", None)
            end_date = data.get("end_date", None)

            # Convert string dates to datetime objects if provided
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)

            events = self.calendar_manager.get_events(calendar_name, start_date, end_date)

            return {
                "status": "success",
                "calendar": calendar_name or "default",
                "events": events
            }
        except ValueError as e:
            logger.error(f"Error in query: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_create(self, data):
        """Handle event creation requests"""
        try:
            calendar_name = data.get("calendar", None)
            event_data = data.get("event", {})

            if not event_data:
                return {"status": "error", "message": "No event data provided"}

            event_id = self.calendar_manager.add_event(calendar_name, event_data)

            return {
                "status": "success",
                "message": f"Event '{event_data.get('summary', 'New Event')}' created successfully",
                "event_id": event_id
            }
        except ValueError as e:
            logger.error(f"Error in create: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_update(self, data):
        """Handle event update requests"""
        try:
            calendar_name = data.get("calendar", None)
            event_id = data.get("event_id", None)
            event_data = data.get("event", {})

            if not event_id or not event_data:
                return {"status": "error", "message": "Event ID and data are required"}

            success = self.calendar_manager.set_event(calendar_name, event_id, event_data)

            if success:
                return {
                    "status": "success",
                    "message": f"Event '{event_id}' updated successfully"
                }
            else:
                return {"status": "error", "message": "Failed to update event"}
        except ValueError as e:
            logger.error(f"Error in update: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_delete(self, data):
        """Handle event deletion requests"""
        try:
            calendar_name = data.get("calendar", None)
            event_id = data.get("event_id", None)

            if not event_id:
                return {"status": "error", "message": "Event ID is required"}

            success = self.calendar_manager.delete_event(calendar_name, event_id)

            if success:
                return {
                    "status": "success",
                    "message": f"Event '{event_id}' deleted successfully"
                }
            else:
                return {"status": "error", "message": "Failed to delete event"}
        except ValueError as e:
            logger.error(f"Error in delete: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return {"status": "error", "message": str(e)}

async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    logger.info(f"New connection from {websocket.remote_address}")

    # Create a bridge instance for this connection
    bridge = MCPRadicaleBridge()
    if not await bridge.connect():
        await websocket.send(json.dumps({"status": "error", "message": "Failed to connect to Radicale"}))
        return

    try:
        async for message in websocket:
            logger.info(f"Received message: {message}")

            # Process the request
            response = await bridge.handle_mcp_request(message)

            # Send response back to client
            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    except Exception as e:
        logger.error(f"Error handling websocket: {e}")

async def main():
    """Start the MCP server"""
    logger.info(f"Starting MCP server on {MCP_HOST}:{MCP_PORT}")

    async with websockets.serve(websocket_handler, MCP_HOST, MCP_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())