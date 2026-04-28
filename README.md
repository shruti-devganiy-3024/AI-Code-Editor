╔══════════════════════════════════════════════════════════════════╗
║                    AI CODE EDITOR v2.0                          ║
║              Offline AI-Powered Code Editor                     ║
║                  Built with Python                              ║
╚══════════════════════════════════════════════════════════════════╝


Welcome to AI Code Editor a lightweight, fully offline code 
editor with a built-in AI assistant. No internet required. 
No API keys. No subscriptions. Just install and code!

Works on Windows 32-bit and 64-bit systems.


══════════════════════════════════════════════════════════════════
📋 TABLE OF CONTENTS
══════════════════════════════════════════════════════════════════

  1. Features
  2. Requirements
  3. Quick Start (Run Directly)
  4. Build Standalone EXE
  5. How to Use the AI Assistant
  6. Supported Languages
  7. Keyboard Shortcuts
  8. Folder Structure
  9. Troubleshooting
  10. About


══════════════════════════════════════════════════════════════════
1. ✨ FEATURES
══════════════════════════════════════════════════════════════════

  🤖 AI ASSISTANT (100% Offline)
     • Chat with AI about any coding topic
     • Get instant help with errors and bugs
     • AI explains concepts in simple terms
     • Ask for code examples in any language
     • AI learns from your conversations over time
     • Chat history saved and searchable

  📝 CODE EDITOR
     • Syntax highlighting for C, C++, Python, Java, JS, PHP
     • Line numbers
     • Auto-indentation
     • Dark theme (easy on the eyes)
     • Large readable fonts
     • Context menu (right-click Cut/Copy/Paste)

  ⚡ COMPILER & RUNNER
     • One-click compile for C/C++
     • Run Python, JavaScript, PHP directly
     • Build & Run with a single button (F5)
     • Output panel shows results and errors

  💡 SMART SUGGESTIONS
     • Code analysis detects common mistakes
     • Missing includes/imports detection
     • Bracket and parenthesis matching
     • Memory leak warnings
     • Style and best practice tips

  📂 PROJECT MANAGEMENT
     • Open project folders
     • Open header files
     • File browser in output panel
     • Save/load chat sessions

  🧠 AI KNOWLEDGE BASE
     • 50+ coding concepts explained
     • 20+ ready-to-use code templates
     • 30+ error diagnostics
     • Covers: Data structures, algorithms, OOP,
       design patterns, Git, regex, and more
     • AI gets smarter the more you use it!


══════════════════════════════════════════════════════════════════
2. 📦 REQUIREMENTS
══════════════════════════════════════════════════════════════════

  MINIMUM:
  ✅ Python 3.8 or higher
     Free download: https://www.python.org/downloads/

  OPTIONAL (for compiling C/C++):
  ✅ GCC or Clang compiler
     • Windows: Install MinGW or MSYS2
     • Linux: Usually pre-installed (gcc/g++)

  ❌ NO internet connection needed
  ❌ NO Ollama or external AI tools needed
  ❌ NO API keys or accounts required
  ❌ NO paid subscriptions

  This editor runs 100% offline on your local machine.


══════════════════════════════════════════════════════════════════
3. 🚀 QUICK START (Easiest Method)
══════════════════════════════════════════════════════════════════

  STEP 1: Install Python
  ─────────────────────
  • Download from: https://www.python.org/downloads/
  • During installation:
    ⚠ CHECK the box "Add Python to PATH" ← IMPORTANT!
  • Click "Install Now"

  STEP 2: Run the Editor
  ─────────────────────
  Option A: Double-click RUN_EDITOR.bat

  Option B: Open Command Prompt and type:
                python AI_Code_Editor_Offline.py

  That's it! The editor will open and you can start coding.


══════════════════════════════════════════════════════════════════
4. 🔨 BUILD STANDALONE EXE (Optional)
══════════════════════════════════════════════════════════════════

  Want a standalone .exe that runs without Python installed?

  STEP 1: Make sure Python is installed (see above)

  STEP 2: Double-click BUILD_EXE.bat

  STEP 3: Wait for the build to complete
          (This may take 1-3 minutes)

  STEP 4: Find your EXE at:
          📁 dist\AICodeEditor.exe

  STEP 5: Copy AICodeEditor.exe anywhere you want!
          Share it with friends — no Python needed to run it.

  NOTE: First launch of the EXE may take a few seconds.


══════════════════════════════════════════════════════════════════
5. 🤖 HOW TO USE THE AI ASSISTANT
══════════════════════════════════════════════════════════════════

  The AI chat panel is on the RIGHT side of the editor.
  Type your question and press Ctrl+Enter (or click Send).

  ── THINGS YOU CAN ASK ──

  💬 General:
     • "hi" or "hello"
     • "what can you do"
     • "tell me a joke"

  📝 Request Code:
     • "write hello world in C"
     • "create a calculator in python"
     • "make a linked list in C"
     • "write binary search"
     • "write bubble sort"
     • "create a todo list in python"
     • "write a login system in python"
     • "write a web page in HTML"

  📖 Learn Concepts:
     • "explain pointers"
     • "what is OOP"
     • "what is a linked list"
     • "explain big O notation"
     • "what is recursion"
     • "explain design patterns"
     • "difference between C and C++"
     • "difference between array and linked list"
     • "difference between stack and queue"

  🔧 Get Help with Errors:
     • "fix segfault"
     • "what is a null pointer"
     • "explain syntax error"
     • "fix memory leak"
     • "what does TypeError mean"
     • "why am I getting undefined reference"

  💻 Code Analysis:
     • Write code in the editor, then ask:
       "check my code"
       "analyze my code"
       "what's wrong with my code"
       "review this"

  🔄 Other:
     • "how to compile"
     • "how to learn C"
     • "how to learn python"
     • "when to use pointers"
     • "what does ++ do"
     • "what does sizeof do"
     • "best practices"
     • "naming conventions"

  ── TIPS ──

  • Be specific! "write calculator in C" works better
    than just "write code"
  • The AI remembers your conversation context
  • Chat history is saved automatically
  • Click "+ New Chat" to start a fresh conversation
  • The more you chat, the smarter the AI gets!


══════════════════════════════════════════════════════════════════
6. 🌐 SUPPORTED LANGUAGES
══════════════════════════════════════════════════════════════════

  Language        Extensions      Run/Compile
  ──────────────────────────────────────────────
  C               .c              gcc → compile & run
  C++             .cpp .hpp       g++/clang++ → compile & run
  Python          .py             python → run directly
  Java            .java           javac + java
  JavaScript      .js             node → run directly
  PHP             .php            php → run directly
  HTML            .html           Opens in browser
  CSS             .css            (used with HTML)
  SQL             .sql            (syntax highlighting)

  The editor provides:
  ✅ Syntax highlighting for all above languages
  ✅ AI help and code generation for all above
  ✅ Direct compile/run for C, C++, Python, JS, PHP


══════════════════════════════════════════════════════════════════
7. ⌨ KEYBOARD SHORTCUTS
══════════════════════════════════════════════════════════════════

  FILE:
  ─────
  Ctrl + N          New file
  Ctrl + O          Open file
  Ctrl + S          Save file

  BUILD:
  ─────
  Ctrl + B          Compile
  Ctrl + R          Run
  F5                Build & Run (compile + run)

  EDITOR:
  ─────
  Ctrl + Z          Undo
  Ctrl + Y          Redo
  Ctrl + A          Select all
  Ctrl + C          Copy
  Ctrl + V          Paste
  Ctrl + X          Cut
  Right-click       Context menu

  CHAT:
  ─────
  Ctrl + Enter      Send message to AI


══════════════════════════════════════════════════════════════════
8. 📁 FOLDER STRUCTURE
══════════════════════════════════════════════════════════════════

  AI_CODE_EDITOR_PROJECT/
  │
  ├── AI_Code_Editor_Offline.py   ← Main application
  ├── RUN_EDITOR.bat               ← Quick launcher
  ├── BUILD_EXE.bat                ← EXE builder
  ├── README.md                    ← Documentation
  ├── requirements.txt             ← Dependencies
  ├── .gitignore                   ← Git ignore rules
  │
  ├── chats/                       ← Saved chat sessions
  │   └── *.json
  │
  ├── code/                        ← Your code files
  │
  ├── headers/                     ← Header files
  │   ├── editor_generated/
  │   ├── system_cpp/
  │   ├── user_headers/
  │   └── visual_cpp/
  │
  ├── data/
  │   └── knowledge.json           ← AI learned knowledge
  │
  ├── build/                       ← PyInstaller temp (auto-generated)
  │
  └── dist/
      └── AICodeEditor.exe         ← Standalone executable


══════════════════════════════════════════════════════════════════
9. 🔧 TROUBLESHOOTING
══════════════════════════════════════════════════════════════════

  PROBLEM: "python is not recognized"
  FIX: Python is not in your PATH.
       → Reinstall Python and CHECK "Add Python to PATH"
       → Or use the full path: C:\Python39\python.exe

  PROBLEM: Editor won't open
  FIX: Open Command Prompt, navigate to the folder, and run:
       python ai_code_editor.py
       Check for any error messages.

  PROBLEM: Compile button doesn't work
  FIX: You need a C/C++ compiler installed.
       → Install MinGW: https://www.mingw-w64.org/
       → Or install MSYS2: https://www.msys2.org/
       → Make sure gcc/g++ is in your PATH

  PROBLEM: "Compiler not found"
  FIX: The editor looks for clang++ by default.
       → Install clang, OR
       → Install g++ (MinGW), the editor will detect it

  PROBLEM: AI gives generic responses
  FIX: Make sure you don't have duplicate method definitions.
       → Use the latest version of ai_code_editor.py
       → Delete the data/knowledge.json file to reset AI memory

  PROBLEM: Chat history not saving
  FIX: Make sure the "chats" folder exists in the same
       directory as ai_code_editor.py

  PROBLEM: BUILD_EXE.bat fails
  FIX: 
       → Run: pip install pyinstaller
       → Then try BUILD_EXE.bat again
       → Or manually: pyinstaller --onefile ai_code_editor.py

  PROBLEM: EXE is flagged by antivirus
  FIX: This is a false positive (common with PyInstaller).
       → Add an exception in your antivirus
       → The source code is open — verify it yourself!


══════════════════════════════════════════════════════════════════
10. ℹ ABOUT
══════════════════════════════════════════════════════════════════

  AI Code Editor v2.0
  
  A fully offline, AI-powered code editor built with Python.
  
  • No internet required
  • No external AI APIs or services
  • No cloud connections
  • No data collection
  • 100% runs on your local machine
  • Works on low-end systems
  • Free and open source

  The AI assistant uses a smart pattern-matching and keyword
  recognition system with a built-in knowledge base. It learns
  from your conversations and gets better over time.

  All your data (code, chats, knowledge) stays on YOUR computer.
  Nothing is sent anywhere. Complete privacy.

  Built with:
  • Python 3
  • Tkinter (GUI)
  • Love for coding ❤


## 🛠️ About This Project

This is an offline AI-powered code editor I developed as a freelance project.

**My contributions:**
- Removed external AI dependencies (Ollama)
- Built offline AI assistant with knowledge base
- Added chat history & session management
- Multi-language editor support (C, C++, Python, Java, JS, PHP, HTML, SQL)
- Complete UI redesign with dark theme
- Code analysis & suggestions system

══════════════════════════════════════════════════════════════════
  Thank you for using AI Code Editor!
  Happy Coding! 🚀
══════════════════════════════════════════════════════════════════