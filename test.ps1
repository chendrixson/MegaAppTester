# Define the VM name
$vmName = "Win11 Dev"

# Get the VM object using WMI
$vm = Get-WmiObject -Namespace "root\virtualization\v2" `
                       -Class "Msvm_VirtualMachine" `
                       -Filter "ElementName='$vmName'"

# Get the VM's console object
$console = $vm.GetConsole()

# Get the console's bitmap object
$bitmap = $console.GetBitmap()

# Save the bitmap to a file
$bitmap.Save("Screenshot.png")
