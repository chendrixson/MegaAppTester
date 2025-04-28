print("Script starting...")
from hyperv import HyperVConnection
from omniparser import Omniparser
from image_viewer import ImageViewer
from console_window import ConsoleWindow
from vmconnect_capture import click_at_coordinates, send_text, press_key, open_run_dialog
from llmcontroller import LLMController
import time
from enum import Enum, auto

class MegaAppTester:
    class AppMode(Enum):
        UNINITIALIZED = auto()
        SINGLE_ACTION = auto()  # First mode
        PERFORM_TASK = auto()
        APP_INSTALL_TEST = auto()

    # Map of shortcut names to winget package IDs and friendly names
    app_map = {
        "vscode": {"winget_id": "Microsoft.VisualStudioCode", "shortcut_name": "Visual Studio Code"},
        "chrome": {"winget_id": "Google.Chrome", "shortcut_name": "Google Chrome"},
        "firefox": {"winget_id": "Mozilla.Firefox", "shortcut_name": "Mozilla Firefox"},
        "notepad++": {"winget_id": "Notepad++.Notepad++", "shortcut_name": "Notepad++"},
        "7zip": {"winget_id": "7zip.7zip", "shortcut_name": "7-Zip"},
        "vlc": {"winget_id": "VideoLAN.VLC", "shortcut_name": "VLC Media Player"},
        "git": {"winget_id": "Git.Git", "shortcut_name": "Git"},
        "python": {"winget_id": "Python.Python.3.11", "shortcut_name": "Python 3.11"},
        "nodejs": {"winget_id": "OpenJS.NodeJS", "shortcut_name": "Node.js"},
        "steam": {"winget_id": "Valve.Steam", "shortcut_name": "Steam"},
        "spotify": {"winget_id": "Spotify.Spotify", "shortcut_name": "Spotify"},
        "discord": {"winget_id": "Discord.Discord", "shortcut_name": "Discord"},
        "slack": {"winget_id": "SlackTechnologies.Slack", "shortcut_name": "Slack"},
        "zoom": {"winget_id": "Zoom.Zoom", "shortcut_name": "Zoom"},
        "obs": {"winget_id": "OBSProject.OBSStudio", "shortcut_name": "OBS Studio"}
    }

    def get_winget_id(self, app_name: str) -> str:
        """Get the winget package ID for a given app shortcut name.
        
        Args:
            app_name (str): The shortcut name or winget ID of the app
            
        Returns:
            str: The winget package ID if found, otherwise returns the original app_name
        """
        app_info = self.app_map.get(app_name.lower())
        return app_info["winget_id"] if app_info else app_name

    def get_app_shortcut_name(self, app_name: str) -> str:
        """Get the friendly shortcut name for a given app.
        
        Args:
            app_name (str): The shortcut name or winget ID of the app
            
        Returns:
            str: The friendly shortcut name if found, otherwise returns the original app_name
        """
        app_info = self.app_map.get(app_name.lower())
        return app_info["shortcut_name"] if app_info else app_name

    def __init__(self):
        self.current_mode = self.AppMode.UNINITIALIZED
        self.console = None
        self.viewer = None
        self.connection = None
        self.parser = None
        self.parsed_content = None
        self.screenshot_width = 0
        self.screenshot_height = 0
        self.llm_controller = LLMController()
        self.llm_controller.setup()

    def initialize(self, connection, viewer, console, parser):
        """Initialize the app with all required components"""
        self.connection = connection
        self.viewer = viewer
        self.console = console
        self.parser = parser
        self.console.set_command_handler(self.handle_command)
        self.show_mode_selection()

    def run_loop(self, duration_seconds=None):
        """Run the main processing loop for a specified duration.
        
        Args:
            duration_seconds: Optional float, number of seconds to run. If None, runs indefinitely.
            
        Returns:
            bool: True if loop completed normally, False if interrupted
        """
        start_time = time.perf_counter()
        
        try:
            while True:
                # Check if we've exceeded the duration
                if duration_seconds is not None:
                    if time.perf_counter() - start_time >= duration_seconds:
                        return True
                
                # Update both windows
                self.viewer.update()
                self.console.update()
                
                # Get new screenshot and time it
                start_time_screenshot = time.perf_counter()
                screenshot = self.connection.get_screenshot()
                screenshot_time = (time.perf_counter() - start_time_screenshot) * 1000
                
                if screenshot:
                    # Store screenshot dimensions
                    self.screenshot_width, self.screenshot_height = screenshot.size
                    
                    # Parse the screenshot and time it
                    start_time_parse = time.perf_counter()
                    try:
                        labeled_img, parsed_content = self.parser.parse(screenshot)
                        parse_time = (time.perf_counter() - start_time_parse) * 1000
                        
                        # Display the labeled image instead of raw screenshot
                        self.viewer.update_image(labeled_img)
                        # Add id field to each element based on index
                        for i, element in enumerate(parsed_content):
                            element["id"] = i
                        self.parsed_content = parsed_content
                    except Exception as e:
                        error_msg = f"Failed to parse screenshot: {str(e)}"
                        print(error_msg)
                        # If parsing fails, show raw screenshot as fallback
                        self.viewer.update_image(screenshot)
                        
        except KeyboardInterrupt:
            return False
            
        return True

    def handle_mode_selection(self, cmd: str):
        """Handle mode selection commands when in UNINITIALIZED state"""
        if cmd == "1":
            self.current_mode = self.AppMode.SINGLE_ACTION
            self.console.write_line("Switched to Single Action mode", system=True)
            self.show_single_action_help()
        elif cmd == "2":
            self.current_mode = self.AppMode.PERFORM_TASK
            self.console.write_line("Switched to Perform Task mode", system=True)
            self.show_perform_task_help()
        elif cmd == "3":
            self.current_mode = self.AppMode.APP_INSTALL_TEST
            self.console.write_line("Switched to App Install Test mode", system=True)
            self.show_app_install_help()
        else:
            self.console.write_line("Invalid mode selection. Please choose 1, 2, or 3", system=True)

    def handle_perform_task_command(self, cmd: str):
        """Handle commands when in PERFORM_TASK mode"""
        self.console.write_line(f"Requesting to Perform Task: {cmd}", system=True)
        while True:
            action = self.do_task(cmd)
            self.console.write_line(f"Action: {action}", system=True)
            self.run_loop(1.0)  # Run the loop for 1 second to allow the action to be performed
            return

    def handle_single_action_command(self, cmd: str):
        """Handle commands when in SINGLE_ACTION mode"""
        self.console.write_line(f"Requesting Single Action: {cmd}", system=True)
        action = self.do_action(cmd)
        self.console.write_line(f"Action: {action}", system=True)

    def do_action(self, cmd: str):
        """Execute a single action and return the action taken.
        
        Args:
            cmd (str): The command/task to execute
            
        Returns:
            str or dict: The action taken. Either "task_complete" or a dict with action details
        """
        action_str = self.llm_controller.get_action_response(cmd, self.parsed_content)
        if "task_complete" in action_str:
            self.console.write_line("No Action", system=True)
            return action_str
            
        return self.process_action_response(action_str)

    def handle_single_action_command(self, cmd: str):
        """Handle commands when in SINGLE_ACTION mode"""
        self.console.write_line(f"Requesting Single Action: {cmd}", system=True)
        action = self.do_action(cmd)
        self.console.write_line(f"Action: {action}", system=True)

    def do_task(self, task: str):
        """Execute a task and return the action count.
        
        Args:
            cmd (str): The command/task to execute
        """
        action_count = 0
        while True:
            action_str = self.llm_controller.get_task_response(task, self.parsed_content)
            if "task_complete" in action_str:
                self.console.write_line("Task Complete from LLM", system=True)
                return action_count
            if "task_wait" in action_str:
                action_count += 1
                self.console.write_line("Waiting...", system=True)
                self.run_loop(2.0)  # Run the loop for 1 second to allow time to pass
                continue
            action_count += 1
            action = self.process_action_response(action_str)
            self.console.write_line(f"Action: {action}", system=True)
            self.run_loop(1.0)  # Run the loop for 1 second to allow the action to be performed
            if action_count > 4:

                self.console.write_line(f"Too many actions {action_count} complete", system=True)
                return action_count

    def process_action_response(self, action_str: str):
        """Process an action string from the LLM and execute it.
        
        Args:
            action_str (str): The action string from the LLM response
            
        Returns:
            str or dict: The action taken. Either "task_complete" or a dict with action details
        """
        # Strip off "json" prefix if present
        if action_str.lower().startswith('```json'):
            action_str = action_str[7:].rstrip('`').strip()
        elif action_str.lower().startswith('json'):
            action_str = action_str[4:].lstrip()

        try:
            import json
            action = json.loads(action_str)
            # Handle the action based on type
            if action["action"] == "click":
                self.click_on_control(action["id"])
            elif action["action"] == "type":
                # Get text from action and send to VM
                text = action.get("text", "")
                if text:
                    send_text(text)
                pass
            elif action["action"] == "select":
                self.click_on_control(action["id"])
                pass
            elif action["action"] == "keypress":
                # Get key from action and send to VM
                key = action.get("key", "")
                if key:
                    press_key(key)
                pass
            return action
        except json.JSONDecodeError:
            self.console.write_line(f"Error: Invalid action format from LLM: {action_str}", system=True)
            return "invalid_json"

    def click_on_control(self, control_id: int):
        """Click on a control using its ID from the parsed content.
        
        Args:
            control_id (int): The ID of the control to click on
        """
        if not self.parsed_content:
            self.console.write_line("Error: No parsed content available", system=True)
            return

        # Find the control with the matching ID
        control = None
        for item in self.parsed_content:
            if item.get("id") == control_id:
                control = item
                break

        if not control:
            self.console.write_line(f"Error: Control with ID {control_id} not found", system=True)
            return

        # Log the control name/content being clicked
        control_content = control.get("content", "Unknown control")
        self.console.write_line(f"Clicking on control: {control_content}", system=True)

        # Get the bounding box coordinates from bbox array
        bbox = control.get("bbox", [0, 0, 0, 0])
        x1 = bbox[0]
        y1 = bbox[1] 
        x2 = bbox[2]
        y2 = bbox[3]

        # Scale coordinates from 0-1 range to actual screenshot dimensions
        x1 = x1 * self.screenshot_width
        y1 = y1 * self.screenshot_height
        x2 = x2 * self.screenshot_width 
        y2 = y2 * self.screenshot_height

        # Calculate center point
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Draw circle at click location, this needs to be done before we scale down coordinates
        self.viewer.draw_circle(center_x, center_y)

        # Scale coordinates by 1.5 since the viewer is scaled down by 1.5
        scaled_x = int(center_x / 1.5)
        scaled_y = int(center_y / 1.5)

        # Add small delay before clicking to allow circle to be visible
        time.sleep(3)

        # Click at the scaled coordinates
        click_at_coordinates(scaled_x, scaled_y)
        self.console.write_line(f"Clicked control {control_id} at ({scaled_x}, {scaled_y})", system=True)

    def handle_app_install_command(self, app_name: str):
        """Handle commands when in APP_INSTALL_TEST mode"""
        # Check for revert command
        if app_name.lower() == "revert":
            self.console.write_line("Reverting VM to previous snapshot...", system=True)
            self.connection.apply_checkpoint("revert")
            self.console.write_line("VM reverted successfully", system=True)
            return
            
        winget_id = self.get_winget_id(app_name)
        shortcut_name = self.get_app_shortcut_name(app_name)
        
        if winget_id != app_name:
            self.console.write_line(f"Installing {shortcut_name} using package ID: {winget_id}", system=True)
        else:
            self.console.write_line(f"Installing package: {app_name}", system=True)
            
        self.console.write_line("Opening Run Dialog", system=True)
        open_run_dialog()
        self.run_loop(1.0)
        send_text("cmd")
        press_key("enter")
        self.console.write_line("Kicking off winget install", system=True)
        send_text("winget install --accept-source-agreements " + winget_id)
        press_key("enter")
        self.run_loop(10.0)
        self.console.write_line("AI Driving through installer", system=True)
        self.do_task(f"Run through the application installer by clicking next, yes, Ok, or whatever is appropriate to move to the next step." \
            "Do not click 'No' or 'Cancel' or just hit the enter key.  If you do, the installer will exit and the task will fail." \
            "If it looks like the installer is working and we should wait, respond with 'task_wait'." \
            "When it looks like the installation is complete, respond with 'task_complete'.  You can tell if this installation is completed" \
            f"by looking for the {shortcut_name} icon on the desktop, or not seeing any more installer steps.")
        self.console.write_line("Installation complete, launching application", system=True)
        press_key("windows")
        send_text(shortcut_name)
        press_key("enter")
        self.run_loop(1.0)
        self.console.write_line("Test complete", system=True)

    def show_perform_task_help(self):
        """Show available commands for Perform Task mode"""
        self.console.write_line("Perform Task Commands:", system=True)
        self.console.write_line("  help - Show this help message", system=True)
        self.console.write_line("  exit - Return to mode selection", system=True)

    def show_app_install_help(self):
        """Show available commands for App Install Test mode"""
        self.console.write_line("App Install Test Commands:", system=True)
        self.console.write_line("  help - Show this help message", system=True)
        self.console.write_line("  exit - Return to mode selection", system=True)
        self.console.write_line("Any other text will be interpreted as an app to install (eg. Chrome)", system=True)

    def show_single_action_help(self):
        """Show available commands for Single Action mode"""
        self.console.write_line("Single Action Commands:", system=True)
        self.console.write_line("  help - Show this help message", system=True)
        self.console.write_line("  exit - Return to mode selection", system=True)
        self.console.write_line("Any other text will be interpreted as a single action to perform", system=True)

    def handle_command(self, cmd: str):
        """Main command handler that routes commands based on current mode"""
        if cmd.lower() == "exit" and self.current_mode != self.AppMode.UNINITIALIZED:
            self.current_mode = self.AppMode.UNINITIALIZED
            self.console.write_line("Returned to mode selection.", system=True)
            self.console.clear()
            self.show_mode_selection()
            return

        if self.current_mode == self.AppMode.UNINITIALIZED:
            self.handle_mode_selection(cmd)
        elif self.current_mode == self.AppMode.PERFORM_TASK:
            self.handle_perform_task_command(cmd)
        elif self.current_mode == self.AppMode.APP_INSTALL_TEST:
            self.handle_app_install_command(cmd)
        elif self.current_mode == self.AppMode.SINGLE_ACTION:
            self.handle_single_action_command(cmd)

    def show_mode_selection(self):
        """Show the mode selection menu"""
        self.console.write_line("Select Control Mode:", system=True)
        self.console.write_line("1) Single Action", system=True)
        self.console.write_line("2) Perform Task", system=True)
        self.console.write_line("3) App Install Test", system=True)

def main(vm_name: str):
    """Main entrypoint that connects to and interacts with a Hyper-V VM"""
    print(f"Attempting to connect to VM: {vm_name}")

    connection = HyperVConnection(vm_name)
    if not connection.connect():
        print(f"Failed to connect to VM '{vm_name}'")
        return

    print("Successfully connected to VM!")

    # create the parser that we'll use during operation
    config = {
        'som_model_path': 'weights/icon_detect/model.pt',
        'caption_model_name': 'florence2',
        'caption_model_path': 'weights/icon_caption_florence',
        'BOX_TRESHOLD': 0.05
    }
    start_time = time.perf_counter()
    parser = Omniparser(config)
    parse_time = (time.perf_counter() - start_time) * 1000
    print(f"Loading OmniParser took {parse_time:.0f}ms")

    # Create image viewer window, this will display our view of the parsed image
    viewer = ImageViewer(window_title=f"VM View: {vm_name}")

    # Create console window for command input/output
    console = ConsoleWindow(window_title=f"VM Console: {vm_name}")

    # Set up click handler to tunnel clicks to VM
    def handle_click(x: int, y: int):
        print(f"Clicking at ({x}, {y})")
        click_at_coordinates(x, y)
        console.write_line(f"Clicked at ({x}, {y})", system=True)
    
    viewer.set_click_handler(handle_click)

    # Create and initialize the app
    app = MegaAppTester()
    
    # Get a screenshot and time it, just to initialize the viewer
    start_time = time.perf_counter()
    screenshot = connection.get_screenshot()
    screenshot_time = (time.perf_counter() - start_time) * 1000

    # Resize viewer window to match screenshot size
    width, height = screenshot.size
    width = int(width / 1.5)
    height = int(height / 1.5)
    viewer.root.geometry(f"{width}x{height}")

    # Initialize the app with all components
    app.initialize(connection, viewer, console, parser)

    try:
        # Run the main loop indefinitely
        app.run_loop()
    except KeyboardInterrupt:
        print("\nClosing windows...")
    finally:
        viewer.close()
        console.close()
    
    return connection

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: script.py <vm_name>")
        sys.exit(1)
    
    main(sys.argv[1])
