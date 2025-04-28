import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable

class ConsoleWindow:
    def __init__(self, window_title="Console Window", window_size=(600, 400)):
        """Initialize the console window
        
        Args:
            window_title (str): Title of the window
            window_size (tuple): Initial window size as (width, height)
        """
        self.root = tk.Tk()
        self.root.title(window_title)
        self.root.geometry(f"{window_size[0]}x{window_size[1]}")
        
        # Create main frame
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create output text area with scrollbar
        self.output_area = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            height=15
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create input frame for command entry
        self.input_frame = ttk.Frame(self.frame)
        self.input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Create command prompt label
        self.prompt_label = ttk.Label(self.input_frame, text=">")
        self.prompt_label.pack(side=tk.LEFT)
        
        # Create command entry
        self.command_entry = ttk.Entry(self.input_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Bind Enter key to command execution
        self.command_entry.bind('<Return>', self._on_command)
        
        # Command handler callback
        self.command_callback = None
        
        # Configure tag for system output (gray color)
        self.output_area.tag_configure('system', foreground='gray')
        
    def set_command_handler(self, callback: Callable[[str], None]):
        """Set the callback function for command execution
        
        Args:
            callback: Function that takes command string as argument
        """
        self.command_callback = callback
        
    def _on_command(self, event):
        """Internal command handler that processes command and clears input"""
        command = self.command_entry.get().strip()
        if command:
            # Clear the input field
            self.command_entry.delete(0, tk.END)
            
            # Echo the command
            self.write_line(f"> {command}")
            
            # Execute command if handler is set
            if self.command_callback:
                self.command_callback(command)
    
    def write_line(self, text: str, system: bool = False):
        """Write a line to the output area
        
        Args:
            text: Text to write
            system: If True, format as system output
        """
        self.output_area.insert(tk.END, text + '\n', 'system' if system else '')
        self.output_area.see(tk.END)  # Scroll to bottom
        
    def clear(self):
        """Clear the output area"""
        self.output_area.delete('1.0', tk.END)
        
    def update(self):
        """Update the window - call this in your main loop"""
        self.root.update()
        
    def close(self):
        """Close the window"""
        self.root.destroy()

if __name__ == "__main__":
    # Example usage
    console = ConsoleWindow(window_title="Command Console")
    
    def handle_command(cmd: str):
        # Process the command here
        console.write_line(f"Processing command: {cmd}")

    console.set_command_handler(handle_command)
    console.write_line("Console window initialized", system=True)
    
    try:
        while True:
            console.update()
    except KeyboardInterrupt:
        console.close() 