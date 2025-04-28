# MegaAppTester

A comprehensive application testing and automation framework that combines Hyper-V virtual machine control, UI automation, and AI-powered task execution.

## Features

- **Hyper-V Integration**: Control and interact with virtual machines through Hyper-V
- **UI Automation**: Automated mouse clicks, keyboard input, and window control
- **Application Installation**: Automated installation of common applications via winget
- **AI-Powered Task Execution**: LLM-based task understanding and execution
- **Image Processing**: Screenshot capture and analysis capabilities
- **Console Interface**: Interactive command-line interface for control and monitoring

## Prerequisites

- Windows 10/11 with Hyper-V enabled
- Python 3.11 or later
- Administrative privileges for Hyper-V operations
- GPU with CUDA support (recommended for AI features)

## Installation

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

- `megaAppTester.py`: Main application entry point
- `llmcontroller.py`: AI task execution controller
- `hyperv.py`: Hyper-V virtual machine management
- `vmconnect_capture.py`: VM screen capture and interaction
- `image_viewer.py`: Image display and processing
- `console_window.py`: Console interface management
- `utils.py`: Utility functions
- `omniparser.py`: Command parsing utilities
- `box_annotator.py`: Image annotation tools

## Usage

1. Start the application:
   ```bash
   python megaAppTester.py
   ```

2. Available modes:
   - Single Action Mode: Execute individual commands
   - Perform Task Mode: Execute complex tasks using AI
   - App Install Mode: Install applications via winget

3. Supported applications for installation:
   - Visual Studio Code
   - Google Chrome
   - Mozilla Firefox
   - Notepad++
   - 7-Zip
   - VLC Media Player
   - Git
   - Python
   - Node.js
   - Steam
   - Spotify

## Dependencies

- torch & torchvision: Deep learning framework
- pywin32: Windows API integration
- Pillow: Image processing
- psutil: System monitoring
- ultralytics: YOLO object detection
- transformers: AI model support
- easyocr & paddleocr: OCR capabilities
- supervision: Computer vision utilities

## Contributing

Feel free to submit issues and enhancement requests.

## License

[Specify your license here]

## Support

For support, please [specify your support channels]. 