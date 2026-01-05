# Quick Start Guide (Windows 11 + NVIDIA GPU)

This project is a vision-based desktop agent that uses a local LLM (via LM Studio) to observe your screen and control mouse/keyboard. It is **Windows-only** and actively moves the cursor, clicks, and types — run it only when ready to surrender control temporarily.

Tested configuration (strongly recommended for best results):
- Resolution: 1920×1080
- Display scaling: 125%

### Steps

1. **Configure Display**  
   Right-click desktop (Windows Settings) → Display settings → Resolution: 1920×1080, Scale: 125%.

2. **Install LM Studio**  
   - Download and install from https://lmstudio.ai  
   - Download a vision-capable GGUF model (qwen/qwen3-vl-2b-instruct).  
   - Load the model.  
   - Start the local server (click the server icon in the sidebar; default port is 1234).

3. **Download and Extract Repository**  
   - Download the ZIP from GitHub.  
   - Extract all files to a folder (e.g., `C:\desktop-agent`).

4. **Run a Scenario**  
   - Ensure Python 3 is installed (https://www.python.org/downloads/).  
   - Open Command Prompt.  
   - Navigate to the folder:  
     ```
     cd C:\desktop-agent
     ```  
   - Run a scenario (1–9):  
     ```
     python main.py scenarios.json 1
     ```  
     Replace `1` with the desired scenario number (see list below).

### Available Scenarios
1. Basic cursor observation  
2. Center screen cursor movement  
3. Notepad++ window targeting  
4. Click at current position  
5. Text editor preparation and typing  
6. Top-left corner targeting  
7. Bottom-right corner targeting  
8. Window title bar targeting  
9. Diagonal movement verification  

Screenshots are saved to a `dumps` folder for debugging. The agent stops after completing the task or reaching the step limit.

Enjoy experimenting! For details or modifications, see the source files.
