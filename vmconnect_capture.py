import win32gui
import win32ui
import win32con
import win32process
import psutil
from PIL import Image
import numpy as np
from typing import Optional, Tuple, List, Union
import ctypes
import win32api
import time

top_offset = 108
bottom_offset = 37

# Virtual key code constants
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key
VK_LWIN = 0x5B  # Left Windows key
VK_RWIN = 0x5C  # Right Windows key
VK_R = 0x52     # R key

# Key mapping dictionary
KEY_MAP = {
    "enter": VK_RETURN,
    "windows": VK_LWIN,
}

# Define input structure for SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def click_at_coordinates(x: int, y: int) -> bool:
    """Send a mouse click to the specified coordinates in the VMConnect window
    
    Args:
        x: X coordinate within window
        y: Y coordinate within window
        
    Returns:
        bool: True if click was sent successfully, False otherwise
    """
    # Find VMConnect window
    hwnd = find_vmconnect_window()
    if not hwnd:
        print("Could not find VMConnect window")
        return False
        
    # Convert coordinates relative to window
    window_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    border_width = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
    title_height = (window_rect[3] - window_rect[1]) - client_rect[3] - border_width
    
    # Add window frame offset to coordinates
    screen_x = window_rect[0] + border_width + x
    screen_y = window_rect[1] + title_height + y

    #offset by an experimental amount
    screen_y = screen_y + 46
    screen_x = screen_x - 2

    # Get the current cursor position
    old_pos = win32api.GetCursorPos()
    
    try:
        # Move cursor to target position
        win32api.SetCursorPos((screen_x, screen_y))
        
        # Create mouse input structures
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        
        # Mouse down
        ii_.mi = MouseInput(0, 0, 0, win32con.MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(0), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.1)  # Small delay between down and up
        
        # Mouse up
        ii_.mi = MouseInput(0, 0, 0, win32con.MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(0), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        # Move cursor back
        win32api.SetCursorPos(old_pos)
        return True
        
    except Exception as e:
        print(f"Click failed: {str(e)}")
        return False

def is_window_valid(hwnd: int) -> bool:
    """Check if the window handle is valid and visible"""
    try:
        return (
            win32gui.IsWindow(hwnd) and
            win32gui.IsWindowVisible(hwnd) and
            win32gui.GetWindowRect(hwnd) != (0, 0, 0, 0)
        )
    except Exception:
        return False

def find_vmconnect_window() -> Optional[int]:
    """Find the VMConnect window handle"""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            if "Virtual Machine Connection" in window_text:
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(process_id)
                    if process.name().lower() == "vmconnect.exe":
                        hwnds.append(hwnd)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    
    if not hwnds:
        print("No VMConnect windows found")
        return None
        
    # Return first valid window
    for hwnd in hwnds:
        if is_window_valid(hwnd):
            return hwnd
            
    print("Found VMConnect windows but none are valid/visible")
    return None

def capture_window_screenshot(hwnd: int) -> Optional[Image.Image]:
    """Capture a screenshot of the specified window"""
    window_dc = None
    mfc_dc = None
    save_dc = None
    save_bitmap = None
    
    try:
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # Get the DPI scale factor - this seems like it doesn't work right now
#        scale_factor = get_dpi_scale(hwnd)
#        print(f"DPI Scale factor: {scale_factor}")
        
        # Apply scaling
        width = int(width * 1.5)
        height = int(height * 1.5)


        print(f"Window dimensions: {width}x{height} at ({left},{top})")

        # Get the target window DC
        window_dc = win32gui.GetDC(hwnd)
        if not window_dc:
            print("Failed to get window DC")
            return None
            
        # Create DC objects
        mfc_dc = win32ui.CreateDCFromHandle(window_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        # Create bitmap object
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)

        # Try to copy window content using PrintWindow
        try:
            # PW_CLIENTONLY = 1
            # PW_RENDERFULLCONTENT = 2
            result = ctypes.windll.user32.PrintWindow(
                hwnd, 
                save_dc.GetSafeHdc(), 
                2
            )

        except Exception as e:
            print(f"PrintWindow failed with exception: {e}")
            result = 0

        if result:
            try:
                # Convert to PIL Image
                bmpinfo = save_bitmap.GetInfo()
                bmpstr = save_bitmap.GetBitmapBits(True)
                # Create full image first
                full_img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1)
                
                # Crop to remove top and bottom offsets
                img = full_img.crop((0, top_offset, bmpinfo['bmWidth'], bmpinfo['bmHeight'] - bottom_offset))

                return img
            except Exception as e:
                print(f"Failed to convert bitmap to image: {e}")
                return None
        else:
            print("PrintWindow failed to copy window content")
            error_code = ctypes.get_last_error()
            print(f"Last error code: {error_code}")
            return None

    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None
    finally:
        # Clean up in finally block to ensure resources are released
        if save_bitmap:
            win32gui.DeleteObject(save_bitmap.GetHandle())
        if save_dc:
            save_dc.DeleteDC()
        if mfc_dc:
            mfc_dc.DeleteDC()
        if window_dc:
            win32gui.ReleaseDC(hwnd, window_dc)

def get_vmconnect_screenshot() -> Optional[Image.Image]:
    """Get a screenshot from the active VMConnect window"""
    hwnd = find_vmconnect_window()
    if not hwnd:
        print("No VMConnect window found")
        return None
    
    return capture_window_screenshot(hwnd)

def set_foreground_vmconnect() -> Optional[int]:
    """Set VMConnect window as foreground window and return its handle"""
    hwnd = find_vmconnect_window()
    if not hwnd:
        print("Could not find VMConnect window")
        return None
        
    try:
        # Bring window to foreground
        if not win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

        # send a control key down/up event
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, VK_CONTROL, 0)
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, VK_CONTROL, 0)
        
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)  # Give window time to come to foreground
        return hwnd
    except Exception as e:
        print(f"Failed to set foreground window: {e}")
        error_code = ctypes.get_last_error()
        print(f"Last error code: {error_code}")
        return None

def send_special_key(key_code: Union[int, List[int]], press_only: bool = False) -> bool:
    """Send special key press to VMConnect window
    
    Args:
        key_code: Virtual key code(s) to send. Can be single int or list of ints for key combinations
        press_only: If True, only sends key press without release (for modifiers)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not set_foreground_vmconnect():
        return False
        
    try:
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        
        # Convert single key to list
        if isinstance(key_code, int):
            key_codes = [key_code]
        else:
            key_codes = key_code
            
        # Press all keys
        for kc in key_codes:
            ii_.ki = KeyBdInput(kc, 0, 0, 0, ctypes.pointer(extra))
            x = Input(ctypes.c_ulong(1), ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            time.sleep(0.05)
            
        if not press_only:
            # Release all keys in reverse order
            for kc in reversed(key_codes):
                ii_.ki = KeyBdInput(kc, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
                x = Input(ctypes.c_ulong(1), ii_)
                ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                time.sleep(0.05)
                
        return True
        
    except Exception as e:
        print(f"Failed to send special key: {e}")
        return False

def send_text(text: str) -> bool:
    """Send text input to VMConnect window
    
    Args:
        text: String to type into the window
        
    Returns:
        bool: True if successful, False otherwise
    """

    if not set_foreground_vmconnect():
        print("Could not set VMConnect window to foreground")
        return False

    try:
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()

        for char in text:
            # Get virtual key code and shift state
            vk = win32api.VkKeyScan(char)
            if vk == -1:
                print(f"No virtual key code found for character: {char}")
                continue
                
            needs_shift = (vk >> 8) & 0x1  # Check if shift modifier is needed
            vk = vk & 0xFF  # Get base virtual key code
            
            # Press shift if needed
            if needs_shift:
                ii_.ki = KeyBdInput(VK_SHIFT, 0, 0, 0, ctypes.pointer(extra))
                x = Input(ctypes.c_ulong(1), ii_)
                ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                time.sleep(0.05)
            
            # Send key down
            ii_.ki = KeyBdInput(vk, 0, 0, 0, ctypes.pointer(extra))
            x = Input(ctypes.c_ulong(1), ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            time.sleep(0.05)
            
            # Send key up
            ii_.ki = KeyBdInput(vk, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
            x = Input(ctypes.c_ulong(1), ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            time.sleep(0.05)
            
            # Release shift if it was pressed
            if needs_shift:
                ii_.ki = KeyBdInput(VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
                x = Input(ctypes.c_ulong(1), ii_)
                ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                time.sleep(0.05)
                
        return True
        
    except Exception as e:
        print(f"Failed to send text: {e}")
        return False

def press_key(key: str) -> bool:
    """Send a keyboard key press to the VMConnect window
    
    Args:
        key: String identifier of the key to press ('enter' or 'windows')
        
    Returns:
        bool: True if key press was sent successfully, False otherwise
    """
    # Convert key string to virtual key code
    if key.lower() not in KEY_MAP:
        print(f"Unsupported key: {key}")
        return False

    if not set_foreground_vmconnect():
        print("Could not set VMConnect window to foreground")
        return False

    vk_code = KEY_MAP[key.lower()]
    
    try:
        # Create keyboard input structures
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        
        # Key down
        ii_.ki = KeyBdInput(vk_code, 0, 0, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        time.sleep(0.05)  # Small delay between down and up

        # Key up
        ii_.ki = KeyBdInput(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        return True
        
    except Exception as e:
        print(f"Key press failed: {str(e)}")
        return False

def open_run_dialog() -> bool:
    """Send Windows+R key combination to open the Run dialog
    
    Returns:
        bool: True if key combination was sent successfully, False otherwise
    """
    if not set_foreground_vmconnect():
        print("Could not set VMConnect window to foreground")
        return False
        
    try:
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        
        # Press Windows key
        ii_.ki = KeyBdInput(VK_LWIN, 0, 0, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        time.sleep(0.05)
        
        # Press R key
        ii_.ki = KeyBdInput(VK_R, 0, 0, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        time.sleep(0.05)
        
        # Release R key
        ii_.ki = KeyBdInput(VK_R, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        time.sleep(0.05)
        
        # Release Windows key
        ii_.ki = KeyBdInput(VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        return True
        
    except Exception as e:
        print(f"Failed to send Win+R: {str(e)}")
        return False 