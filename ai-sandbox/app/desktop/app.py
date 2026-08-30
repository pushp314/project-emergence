import sys
import asyncio
from PyQt6.QtWidgets import QApplication
import qasync
from app.main import SandboxApp
from app.desktop.main_window import MainWindow

def run_desktop():
    app = QApplication(sys.argv)
    
    # Use qasync to bridge asyncio and Qt
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Initialize Sandbox App
    # start_paused=True so the agents wait for user instructions
    sandbox_app = SandboxApp("./config.yaml", start_paused=True)
    
    async def init_and_run():
        await sandbox_app.initialize()
        window = MainWindow(sandbox_app)
        window.show()
        # Keep reference so window doesn't get garbage collected
        app._main_window = window
        
        # Start the Sandbox background task
        await sandbox_app.run()

    with loop:
        loop.run_until_complete(init_and_run())

if __name__ == "__main__":
    run_desktop()
