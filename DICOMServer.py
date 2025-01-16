import tkinter as tk
import threading
import time
import os
import sys
import asyncio
import json
import subprocess
from websockets.asyncio.server import serve
import numpy as np


class DICOMServer:
    def __init__(self, tkRoot):
        self.clients = set()
        self.server = None
        self.stop_future = None
        self.loop = None
        self.server_thread = None
        self.shutting_down = False  # To prevent shutdown issues
        self.tkRoot = tkRoot

    async def updatetkRoot(self, tkRoot):
        self.base_directory = tkRoot.home
        self.case_directory = tkRoot.case_dir
        try:
            print('updatetkRoot')
        except Exception as e:
            print("Error in updatetkRoot: ", e)
           

    async def handle_json_from_client(self, message, websocket):
        try:
            obj = json.loads(message)
            print("Received JSON data:", obj)

        except json.JSONDecodeError:
            print("Failed to decode JSON message.")

    async def websocket_send(self, websocket, message):
        await websocket.send(json.dumps(message))

    async def websocket_echo(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                await self.handle_json_from_client(message, websocket)
        except Exception as e:
            print(f"WebSocket connection Error: {e}")
        finally:
            self.clients.remove(websocket)


    async def main(self):
        # Create a stop future that will be set when the server should stop
        self.stop_future = self.loop.create_future()

        # Start the WebSocket server
        self.server = await serve(self.websocket_echo, self.tkRoot.host_address, 2025)
        print("WebSocket server started on ws://localhost:2025")

        # Run until the stop future is set
        await self.stop_future

        # Stop the server gracefully
        print("Stopping WebSocket server...")
        self.server.close()
        await self.server.wait_closed()

    def start_websocket_server(self):
        # Start a new event loop for this thread
        self.loop = asyncio.new_event_loop()
        # Set the event loop in this thread
        asyncio.set_event_loop(self.loop)
        # Run the server
        self.loop.run_until_complete(self.main())

    def start(self):
        # Start the server in a new thread
        self.server_thread = threading.Thread(target=self.start_websocket_server)
        self.server_thread.start()

    def stop(self):
        # Prevent multiple shutdown attempts
        if self.shutting_down:
            return
        
        self.shutting_down = True  # Indicate that shutdown is in progress

        # Stopping the server by setting the stop future in the server thread's event loop
        #print("Stopping the websocket server...")
        if self.loop and not self.stop_future.done():
            try:
                # Schedule the stop logic inside the event loop
                asyncio.run_coroutine_threadsafe(self.stop_websocket_server_async(), self.loop).result()
            except Exception as e:
                print(f"Error during shutdown: {e}")
        else:
            print("Event loop is not running or already shutting down.")

        # Wait for the server thread to terminate
        if self.server_thread.is_alive():
            self.server_thread.join()
        #print("Server stopped.")

    async def stop_websocket_server_async(self):
        """Stop server coroutine to be scheduled inside the event loop"""
        if self.stop_future and not self.stop_future.done():
            self.stop_future.set_result(None)

