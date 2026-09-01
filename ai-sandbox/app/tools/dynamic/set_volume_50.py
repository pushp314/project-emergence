from app.tools.gateway import Tool
import subprocess

class SetVolume50Tool(Tool):
    name = 'set_volume_50'
    description = 'Sets the macOS system volume to 50% using osascript.'
    enabled = True
    permission = 'system'
    risk = 'low'
    input_schema = {}

    def execute(self, **kwargs):
        try:
            subprocess.run(['osascript', '-e', 'set volume output volume 50'], check=True)
            return 'Volume set to 50% successfully.'
        except Exception as e:
            return f'Failed to set volume: {str(e)}'

TOOL_INSTANCE = SetVolume50Tool()