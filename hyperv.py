from typing import Optional
import subprocess
import json
from PIL import Image
import io
import win32com.client
import os
from vmconnect_capture import get_vmconnect_screenshot

class HyperVConnection:
    def __init__(self, vm_name: str):
        self.vm_name = vm_name
        self.vm = None
        self.hyperv = None

    def connect(self) -> bool:
        try:
            # Check if VM exists using PowerShell
            result = subprocess.run(
                ['powershell', '-Command', f'Get-VM -Name "{self.vm_name}" | ConvertTo-Json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Failed to find VM: {result.stderr}")
                return False
                           
            return True
        except Exception as e:
            print(f"Failed to connect to VM: {e}")
            return False

    def get_screenshot(self) -> Optional[Image.Image]:
        """
        Take a screenshot of the VM using VMConnect window capture
        Returns:
            Optional[Image.Image]: The screenshot as a PIL Image, or None if failed
        """
        return get_vmconnect_screenshot()

    def send_keys(self, keys: str):
        try:
            # Use PowerShell to send keys
            subprocess.run(
                ['powershell', '-Command', f'$vm = Get-VM -Name "{self.vm_name}"; $vm.KeyboardInput("{keys}")'],
                capture_output=True,
                text=True
            )
        except Exception as e:
            print(f"Failed to send keys: {e}")

    def send_mouse_click(self, x: int, y: int):
        try:
            # Use PowerShell to send mouse click
            subprocess.run(
                ['powershell', '-Command', f'$vm = Get-VM -Name "{self.vm_name}"; $vm.MouseClick({x}, {y})'],
                capture_output=True,
                text=True
            )
        except Exception as e:
            print(f"Failed to send mouse click: {e}")

    def get_vmconnect_screenshot(self) -> Optional[Image.Image]:
        """
        Capture a screenshot from an active VMConnect window
        Returns:
            Optional[Image.Image]: The screenshot as a PIL Image, or None if failed
        """
        return get_vmconnect_screenshot()

    def apply_checkpoint(self, checkpoint_name: str) -> bool:
        """
        Apply a checkpoint to the VM by name
        Args:
            checkpoint_name (str): The name of the checkpoint to apply
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use PowerShell to apply the checkpoint
            result = subprocess.run(
                ['powershell', '-Command', f'Restore-VMSnapshot -VMName "{self.vm_name}" -Name "{checkpoint_name}" -Confirm:$false'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Failed to apply checkpoint: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            print(f"Failed to apply checkpoint: {e}")
            return False

    def revert(self) -> bool:
        """
        Revert the VM to the standard 'revert' checkpoint
        Returns:
            bool: True if successful, False otherwise
        """
        return self.apply_checkpoint("revert")

