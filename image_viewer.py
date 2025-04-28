import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import threading

class ImageViewer:
    def __init__(self, window_title="Image Viewer", window_size=(800, 600)):
        """Initialize the image viewer window
        
        Args:
            window_title (str): Title of the window
            window_size (tuple): Initial window size as (width, height)
        """
        self.root = tk.Tk()
        self.root.title(window_title)
        self.root.geometry(f"{window_size[0]}x{window_size[1]}")
        
        # Create a frame to hold the image
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a label to display the image
        self.image_label = ttk.Label(self.frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Store the PhotoImage reference
        self.photo = None
        
        # Store the current PIL Image
        self.current_image = None
        
        # Click handler callback
        self.click_callback = None
        
        # Bind click event
        self.image_label.bind('<Button-1>', self._on_click)
        
    def set_click_handler(self, callback):
        """Set the callback function for click events"""
        self.click_callback = callback
        
    def _on_click(self, event):
        """Internal click handler that passes raw coordinates to callback"""
        if self.click_callback:
            self.click_callback(event.x, event.y)
        
    def update_image(self, image):
        """Update the displayed image
        
        Args:
            image: Can be a PIL Image, numpy array, or path to image file
        """
        if isinstance(image, np.ndarray):
            # Convert numpy array to PIL Image
            image = Image.fromarray(image)
        elif isinstance(image, str):
            # Load image from file
            image = Image.open(image)
        
        # Store the current image
        self.current_image = image
        
        # Get current display size
        display_size = (self.frame.winfo_width(), self.frame.winfo_height())
        
        # Create a copy before thumbnail to avoid modifying original
        display_image = image.copy()
        display_image.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for display
        self.photo = ImageTk.PhotoImage(display_image)
        self.image_label.configure(image=self.photo)
        
    def update(self):
        """Update the window - call this in your main loop"""
        self.root.update()
        
    def close(self):
        """Close the window"""
        self.root.destroy()

    def draw_circle(self, x: int, y: int, radius: int = 10):
        """Draw a red circle at the specified coordinates.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            radius (int): Radius of the circle in pixels
            duration (float): How long to show the circle in seconds
        """
        if not self.current_image:
            return

        # Create a copy of the current image
        img = self.current_image.copy()
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        
        # Draw red circle
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], outline='red', width=5)
        
        # Update the image
        self.update_image(img)

        # no need to remove circle, it will get pulled off in next frame update

if __name__ == "__main__":
    # Example usage
    viewer = ImageViewer()
    # Create a test image
    test_image = Image.new('RGB', (400, 300), color='red')
    viewer.update_image(test_image)
    
    # Example click handler
    def on_click(x, y):
        print(f"Clicked at ({x}, {y})")
    
    viewer.set_click_handler(on_click)
    
    try:
        while True:
            viewer.update()
    except KeyboardInterrupt:
        viewer.close() 