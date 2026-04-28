#!/usr/bin/env python3
"""
AI Code Editor - Offline AI-style Code Editor
No external AI APIs, No Ollama
Keyword + Memory based smart replies
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import json
import webbrowser
import os
import re
import time
import uuid
from datetime import datetime

# Global readable fonts
EDITOR_FONT = ("Consolas", 18)
UI_FONT = ("Segoe UI", 18)
CHAT_FONT = ("Segoe UI", 18)

# ============================================================
# Folder structure setup
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDERS = {
    "chats": os.path.join(BASE_DIR, "chats"),
    "code": os.path.join(BASE_DIR, "code"),
    "headers": os.path.join(BASE_DIR, "headers"),
    "data": os.path.join(BASE_DIR, "data"),
}

for folder in FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

KNOWLEDGE_FILE = os.path.join(FOLDERS["data"], "knowledge.json")


class SyntaxHighlighter:
    """Simple C/C++ syntax highlighter"""

    KEYWORDS = [
        'auto', 'break', 'case', 'catch', 'class', 'const', 'continue',
        'default', 'delete', 'do', 'else', 'enum', 'explicit', 'extern',
        'false', 'for', 'friend', 'goto', 'if', 'inline', 'mutable',
        'namespace', 'new', 'nullptr', 'operator', 'private', 'protected',
        'public', 'return', 'sizeof', 'static', 'struct', 'switch',
        'template', 'this', 'throw', 'true', 'try', 'typedef', 'typename',
        'union', 'using', 'virtual', 'volatile', 'while', 'override', 'final'
    ]

    TYPES = [
        'bool', 'char', 'double', 'float', 'int', 'long', 'short',
        'signed', 'unsigned', 'void', 'wchar_t', 'string', 'vector',
        'map', 'set', 'list', 'FILE', 'size_t'
    ]

    def __init__(self, text_widget):
        self.text = text_widget
        self.text.tag_configure('keyword', foreground='#569cd6')
        self.text.tag_configure('type', foreground='#4ec9b0')
        self.text.tag_configure('string', foreground='#ce9178')
        self.text.tag_configure('comment', foreground='#6a9955')
        self.text.tag_configure('number', foreground='#b5cea8')
        self.text.tag_configure('preprocessor', foreground='#c586c0')
        self.text.tag_configure('function', foreground='#dcdcaa')

    def highlight(self, event=None):
        for tag in ['keyword', 'type', 'string', 'comment', 'number', 'preprocessor', 'function']:
            self.text.tag_remove(tag, '1.0', 'end')

        content = self.text.get('1.0', 'end')

        for match in re.finditer(r'^\s*#.*$', content, re.MULTILINE):
            self._apply_tag('preprocessor', match)

        for keyword in self.KEYWORDS:
            for match in re.finditer(rf'\b{keyword}\b', content):
                self._apply_tag('keyword', match)

        for type_name in self.TYPES:
            for match in re.finditer(rf'\b{type_name}\b', content):
                self._apply_tag('type', match)

        for match in re.finditer(r'"(?:[^"\\]|\\.)*"', content):
            self._apply_tag('string', match)

        for match in re.finditer(r'//.*$', content, re.MULTILINE):
            self._apply_tag('comment', match)

        for match in re.finditer(r'/\*.*?\*/', content, re.DOTALL):
            self._apply_tag('comment', match)

        for match in re.finditer(r'\b\d+\.?\d*[fFlLuU]*\b', content):
            self._apply_tag('number', match)

        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content):
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.text.tag_add('function', start, end)

    def _apply_tag(self, tag, match):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        self.text.tag_add(tag, start, end)


# ============================================================
# Knowledge Base - learns from conversations
# ============================================================
class KnowledgeBase:
    """Simple keyword-based knowledge system"""

    def __init__(self):
        self.knowledge = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(KNOWLEDGE_FILE):
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    self.knowledge = json.load(f)
        except Exception:
            self.knowledge = {}

    def _save(self):
        try:
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def learn(self, user_msg, ai_reply):
        """Store user message and AI reply as a knowledge pair"""
        key = user_msg.strip().lower()
        if len(key) > 3:
            self.knowledge[key] = ai_reply
            self._save()

    def search(self, query):
        """Search knowledge base by keyword matching"""
        query_lower = query.strip().lower()
        query_words = set(query_lower.split())

        # Exact match
        if query_lower in self.knowledge:
            return self.knowledge[query_lower]

        # Keyword match - find best overlap
        best_match = None
        best_score = 0

        for key, value in self.knowledge.items():
            key_words = set(key.split())
            overlap = len(query_words & key_words)
            if overlap > best_score and overlap >= 2:
                best_score = overlap
                best_match = value

        return best_match


# ============================================================
# AI Service - ULTRA SMART Offline Reply System
# ============================================================
class AIService:
    """
    Smart offline AI with:
    - Context awareness (remembers what you're talking about)
    - Multi-keyword matching (understands complex questions)
    - Code generation ability
    - Conversation flow tracking
    - Emotional intelligence
    - Teaching mode
    - Error diagnosis
    - Follow-up understanding
    """

    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.conversation_history = []
        self.context = {
            "language": None,
            "topic": None,
            "last_question": None,
            "user_level": "beginner",
            "mood": "neutral",
            "code_shared": False,
            "error_mode": False,
            "teach_mode": False
        }
        self.user_name = None
        self.session_count = 0
        self.topics_discussed = []

        self._build_knowledge()

    def _build_knowledge(self):
        """Build massive knowledge database"""

        # =============================================
        # GREETING & SOCIAL RESPONSES
        # =============================================
        self.greetings = {
            "hello": "Hello! 👋 I'm your AI coding assistant. What are you working on today?",
            "hi": "Hi there! Ready to help you code. What do you need?",
            "hey": "Hey! 👋 What are you building today?",
            "good morning": "Good morning! ☀️ Fresh start, fresh code! What shall we work on?",
            "good afternoon": "Good afternoon! How's your coding going?",
            "good evening": "Good evening! 🌙 Late night coding? I'm here to help!",
            "good night": "Good night! 🌙 Don't forget to save and commit your code!",
            "howdy": "Howdy! 🤠 Ready to wrangle some code?",
            "yo": "Yo! What's the code situation?",
            "sup": "Not much, just ready to help you code! What's up?",
            "greetings": "Greetings! I'm your offline AI assistant. Ask me anything about coding!",
        }

        self.social = {
            "how are you": "I'm running great! 💪 My circuits are ready to help you code. What do you need?",
            "what is your name": "I'm CodeAI — your offline coding assistant! No internet needed, just pure local intelligence. 🧠",
            "who are you": "I'm a smart offline AI built into this editor. I can help with C, C++, Python, Java, JS, PHP, SQL, HTML/CSS and more!",
            "who made you": "I was crafted as a lightweight offline AI assistant. No cloud, no API — just local brainpower! 🧠",
            "what can you do": self._get_capabilities(),
            "are you real": "I'm as real as the code you write! 😄 I'm a pattern-matching AI that learns from our chats.",
            "are you ai": "Yes! I'm an offline AI assistant. I don't use the internet — all my knowledge is built-in and I learn from our conversations!",
            "are you smart": "I'm getting smarter every time we chat! 🧠 The more you teach me, the better I get.",
            "do you learn": "Yes! I remember our conversations and learn new things. Try teaching me something!",
            "can you code": "Absolutely! Tell me what you need and I'll write code for you. I know C, C++, Python, Java, JS, PHP, SQL and more!",
            "i love you": "Aww, I love helping you code! ❤️ Let's build something awesome together!",
            "you are awesome": "Thanks! 😊 You're pretty awesome yourself for coding! Keep going!",
            "you are stupid": "I'm sorry if I gave a wrong answer. 😅 Can you help me understand what you need? I'll try harder!",
            "you are wrong": "I apologize! Let me know what's correct and I'll learn from it. I'm always improving!",
            "thank you": "You're welcome! 😊 Happy to help! Anything else?",
            "thanks": "You're welcome! Let me know if you need anything else! 👍",
            "thank": "You're welcome! Keep coding! 💪",
            "bye": "Goodbye! 👋 Happy coding! Your code is saved. See you next time!",
            "goodbye": "See you later! 👋 Don't forget to save your work!",
            "see you": "See you! 👋 I'll be here whenever you need me!",
            "ok": "👍 Got it! Let me know if you need anything else.",
            "okay": "Alright! Need anything else?",
            "cool": "😎 Cool! What's next?",
            "nice": "Thanks! Glad that helped! Anything else?",
            "great": "Awesome! 🎉 What else can I help with?",
            "lol": "😄 Glad I could make you smile! Need anything else?",
            "haha": "😄 Happy to entertain! Back to coding?",
            "hmm": "Take your time thinking! I'm here when you're ready. 🤔",
            "idk": "No worries! Tell me what you're trying to do and I'll guide you step by step.",
            "i don't know": "That's okay! Everyone starts somewhere. What topic should we explore?",
            "i am confused": "Don't worry! Let me help. What exactly is confusing you? I'll explain it simply.",
            "i am stuck": "Let's get you unstuck! 💪 Tell me what you're working on and where you're stuck.",
            "i need help": "I'm here to help! 🆘 Tell me:\n1. What language are you using?\n2. What are you trying to do?\n3. What's going wrong?",
            "i am beginner": "Welcome to programming! 🎉 I'll explain everything in simple terms. What language do you want to learn?",
            "i am learning": "That's great! 📚 Learning is the best thing. What topic are you studying right now?",
            "i am bored": "Let's make coding fun! Try building something:\n• A calculator\n• A guessing game\n• A to-do list\n• A simple website\nWhich sounds interesting?",
            "tell me a joke": "Why do programmers prefer dark mode?\nBecause light attracts bugs! 🐛😄",
            "another joke": "Why do Java developers wear glasses?\nBecause they don't C#! 😄",
            "tell me something": "Did you know? The first computer bug was an actual bug — a moth found in a computer in 1947! 🦋",
            "fun fact": "Fun fact: The Python language is named after Monty Python, not the snake! 🐍",
        }

        # =============================================
        # CODE GENERATION TEMPLATES
        # =============================================
        self.code_templates = {
            "hello world c": (
                "Here's Hello World in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    printf(\"Hello, World!\\n\");\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "Compile: gcc hello.c -o hello\n"
                "Run: ./hello"
            ),
            "hello world cpp": (
                "Here's Hello World in C++:\n\n"
                "```cpp\n"
                "#include <iostream>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    cout << \"Hello, World!\" << endl;\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "Compile: g++ hello.cpp -o hello\n"
                "Run: ./hello"
            ),
            "hello world python": (
                "Here's Hello World in Python:\n\n"
                "```python\n"
                "print(\"Hello, World!\")\n"
                "```\n\n"
                "Run: python hello.py"
            ),
            "hello world java": (
                "Here's Hello World in Java:\n\n"
                "```java\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        System.out.println(\"Hello, World!\");\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "Compile: javac Main.java\n"
                "Run: java Main"
            ),
            "hello world javascript": (
                "Here's Hello World in JavaScript:\n\n"
                "```javascript\n"
                "console.log(\"Hello, World!\");\n"
                "```\n\n"
                "Run in browser console or: node hello.js"
            ),
            "hello world php": (
                "Here's Hello World in PHP:\n\n"
                "```php\n"
                "<?php\n"
                "echo \"Hello, World!\";\n"
                "?>\n"
                "```\n\n"
                "Run: php hello.php"
            ),
            "calculator c": (
                "📝 Simple Calculator in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    double a, b, result;\n"
                "    char op;\n\n"
                "    printf(\"Enter: number operator number\\n\");\n"
                "    printf(\"Example: 5 + 3\\n\");\n"
                "    scanf(\"%lf %c %lf\", &a, &op, &b);\n\n"
                "    switch(op) {\n"
                "        case '+': result = a + b; break;\n"
                "        case '-': result = a - b; break;\n"
                "        case '*': result = a * b; break;\n"
                "        case '/':\n"
                "            if(b == 0) {\n"
                "                printf(\"Error: Division by zero!\\n\");\n"
                "                return 1;\n"
                "            }\n"
                "            result = a / b;\n"
                "            break;\n"
                "        default:\n"
                "            printf(\"Unknown operator!\\n\");\n"
                "            return 1;\n"
                "    }\n\n"
                "    printf(\"%.2f %c %.2f = %.2f\\n\", a, op, b, result);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "calculator python": (
                "📝 Simple Calculator in Python:\n\n"
                "```python\n"
                "def calculator():\n"
                "    print(\"Simple Calculator\")\n"
                "    print(\"Operations: +, -, *, /\")\n\n"
                "    while True:\n"
                "        try:\n"
                "            a = float(input(\"First number: \"))\n"
                "            op = input(\"Operator (+,-,*,/): \")\n"
                "            b = float(input(\"Second number: \"))\n\n"
                "            if op == '+': print(f\"Result: {a + b}\")\n"
                "            elif op == '-': print(f\"Result: {a - b}\")\n"
                "            elif op == '*': print(f\"Result: {a * b}\")\n"
                "            elif op == '/':\n"
                "                if b == 0: print(\"Error: Division by zero!\")\n"
                "                else: print(f\"Result: {a / b}\")\n"
                "            else: print(\"Unknown operator!\")\n\n"
                "            if input(\"Continue? (y/n): \").lower() != 'y':\n"
                "                break\n"
                "        except ValueError:\n"
                "            print(\"Invalid input!\")\n\n"
                "calculator()\n"
                "```"
            ),
            "calculator cpp": (
                "📝 Simple Calculator in C++:\n\n"
                "```cpp\n"
                "#include <iostream>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    double a, b;\n"
                "    char op;\n\n"
                "    cout << \"Enter: number operator number\" << endl;\n"
                "    cin >> a >> op >> b;\n\n"
                "    switch(op) {\n"
                "        case '+': cout << a + b << endl; break;\n"
                "        case '-': cout << a - b << endl; break;\n"
                "        case '*': cout << a * b << endl; break;\n"
                "        case '/': \n"
                "            if(b != 0) cout << a / b << endl;\n"
                "            else cout << \"Error: Division by zero!\" << endl;\n"
                "            break;\n"
                "        default: cout << \"Unknown operator!\" << endl;\n"
                "    }\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "guessing game": (
                "📝 Number Guessing Game in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <time.h>\n\n"
                "int main() {\n"
                "    srand(time(NULL));\n"
                "    int secret = rand() % 100 + 1;\n"
                "    int guess, attempts = 0;\n\n"
                "    printf(\"Guess the number (1-100)!\\n\");\n\n"
                "    do {\n"
                "        printf(\"Your guess: \");\n"
                "        scanf(\"%d\", &guess);\n"
                "        attempts++;\n\n"
                "        if(guess < secret)\n"
                "            printf(\"Too low! Try higher.\\n\");\n"
                "        else if(guess > secret)\n"
                "            printf(\"Too high! Try lower.\\n\");\n"
                "        else\n"
                "            printf(\"Correct! You got it in %d attempts!\\n\", attempts);\n"
                "    } while(guess != secret);\n\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "linked list c": (
                "📝 Linked List in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "typedef struct Node {\n"
                "    int data;\n"
                "    struct Node *next;\n"
                "} Node;\n\n"
                "Node* createNode(int val) {\n"
                "    Node *node = (Node*)malloc(sizeof(Node));\n"
                "    node->data = val;\n"
                "    node->next = NULL;\n"
                "    return node;\n"
                "}\n\n"
                "void insertHead(Node **head, int val) {\n"
                "    Node *node = createNode(val);\n"
                "    node->next = *head;\n"
                "    *head = node;\n"
                "}\n\n"
                "void insertTail(Node **head, int val) {\n"
                "    Node *node = createNode(val);\n"
                "    if(*head == NULL) { *head = node; return; }\n"
                "    Node *temp = *head;\n"
                "    while(temp->next) temp = temp->next;\n"
                "    temp->next = node;\n"
                "}\n\n"
                "void printList(Node *head) {\n"
                "    while(head) {\n"
                "        printf(\"%d -> \", head->data);\n"
                "        head = head->next;\n"
                "    }\n"
                "    printf(\"NULL\\n\");\n"
                "}\n\n"
                "void freeList(Node *head) {\n"
                "    while(head) {\n"
                "        Node *temp = head;\n"
                "        head = head->next;\n"
                "        free(temp);\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    Node *head = NULL;\n"
                "    insertTail(&head, 10);\n"
                "    insertTail(&head, 20);\n"
                "    insertHead(&head, 5);\n"
                "    printList(head);\n"
                "    freeList(head);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "stack c": (
                "📝 Stack Implementation in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#define MAX 100\n\n"
                "typedef struct {\n"
                "    int items[MAX];\n"
                "    int top;\n"
                "} Stack;\n\n"
                "void init(Stack *s) { s->top = -1; }\n"
                "int isEmpty(Stack *s) { return s->top == -1; }\n"
                "int isFull(Stack *s) { return s->top == MAX-1; }\n\n"
                "void push(Stack *s, int val) {\n"
                "    if(isFull(s)) { printf(\"Stack overflow!\\n\"); return; }\n"
                "    s->items[++s->top] = val;\n"
                "}\n\n"
                "int pop(Stack *s) {\n"
                "    if(isEmpty(s)) { printf(\"Stack empty!\\n\"); return -1; }\n"
                "    return s->items[s->top--];\n"
                "}\n\n"
                "int peek(Stack *s) {\n"
                "    if(isEmpty(s)) return -1;\n"
                "    return s->items[s->top];\n"
                "}\n\n"
                "int main() {\n"
                "    Stack s;\n"
                "    init(&s);\n"
                "    push(&s, 10);\n"
                "    push(&s, 20);\n"
                "    push(&s, 30);\n"
                "    printf(\"Top: %d\\n\", peek(&s));\n"
                "    printf(\"Popped: %d\\n\", pop(&s));\n"
                "    printf(\"Top: %d\\n\", peek(&s));\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "queue c": (
                "📝 Queue Implementation in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#define MAX 100\n\n"
                "typedef struct {\n"
                "    int items[MAX];\n"
                "    int front, rear;\n"
                "} Queue;\n\n"
                "void init(Queue *q) { q->front = 0; q->rear = -1; }\n"
                "int isEmpty(Queue *q) { return q->rear < q->front; }\n\n"
                "void enqueue(Queue *q, int val) {\n"
                "    if(q->rear >= MAX-1) { printf(\"Queue full!\\n\"); return; }\n"
                "    q->items[++q->rear] = val;\n"
                "}\n\n"
                "int dequeue(Queue *q) {\n"
                "    if(isEmpty(q)) { printf(\"Queue empty!\\n\"); return -1; }\n"
                "    return q->items[q->front++];\n"
                "}\n\n"
                "int main() {\n"
                "    Queue q;\n"
                "    init(&q);\n"
                "    enqueue(&q, 10);\n"
                "    enqueue(&q, 20);\n"
                "    enqueue(&q, 30);\n"
                "    printf(\"Dequeued: %d\\n\", dequeue(&q));\n"
                "    printf(\"Dequeued: %d\\n\", dequeue(&q));\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "binary search": (
                "📝 Binary Search in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "int binarySearch(int arr[], int n, int target) {\n"
                "    int low = 0, high = n - 1;\n"
                "    while(low <= high) {\n"
                "        int mid = (low + high) / 2;\n"
                "        if(arr[mid] == target) return mid;\n"
                "        else if(arr[mid] < target) low = mid + 1;\n"
                "        else high = mid - 1;\n"
                "    }\n"
                "    return -1;\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {2, 5, 8, 12, 16, 23, 38, 56, 72, 91};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    int target = 23;\n"
                "    int result = binarySearch(arr, n, target);\n"
                "    if(result != -1)\n"
                "        printf(\"Found at index %d\\n\", result);\n"
                "    else\n"
                "        printf(\"Not found\\n\");\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "bubble sort": (
                "📝 Bubble Sort in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "void bubbleSort(int arr[], int n) {\n"
                "    for(int i = 0; i < n-1; i++) {\n"
                "        int swapped = 0;\n"
                "        for(int j = 0; j < n-i-1; j++) {\n"
                "            if(arr[j] > arr[j+1]) {\n"
                "                int temp = arr[j];\n"
                "                arr[j] = arr[j+1];\n"
                "                arr[j+1] = temp;\n"
                "                swapped = 1;\n"
                "            }\n"
                "        }\n"
                "        if(!swapped) break;\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {64, 34, 25, 12, 22, 11, 90};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    bubbleSort(arr, n);\n"
                "    printf(\"Sorted: \");\n"
                "    for(int i = 0; i < n; i++)\n"
                "        printf(\"%d \", arr[i]);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "file read write c": (
                "📝 File Read/Write in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    FILE *fp = fopen(\"data.txt\", \"w\");\n"
                "    if(fp == NULL) {\n"
                "        perror(\"Error opening file\");\n"
                "        return 1;\n"
                "    }\n"
                "    fprintf(fp, \"Hello World\\n\");\n"
                "    fprintf(fp, \"Line 2\\n\");\n"
                "    fprintf(fp, \"Number: %d\\n\", 42);\n"
                "    fclose(fp);\n"
                "    printf(\"File written!\\n\");\n\n"
                "    fp = fopen(\"data.txt\", \"r\");\n"
                "    char line[256];\n"
                "    printf(\"File contents:\\n\");\n"
                "    while(fgets(line, sizeof(line), fp)) {\n"
                "        printf(\"%s\", line);\n"
                "    }\n"
                "    fclose(fp);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "todo list python": (
                "📝 To-Do List in Python:\n\n"
                "```python\n"
                "import json\n"
                "import os\n\n"
                "FILE = 'todos.json'\n\n"
                "def load_todos():\n"
                "    if os.path.exists(FILE):\n"
                "        with open(FILE, 'r') as f:\n"
                "            return json.load(f)\n"
                "    return []\n\n"
                "def save_todos(todos):\n"
                "    with open(FILE, 'w') as f:\n"
                "        json.dump(todos, f, indent=2)\n\n"
                "def main():\n"
                "    todos = load_todos()\n"
                "    while True:\n"
                "        print('\\n=== To-Do List ===')\n"
                "        for i, t in enumerate(todos, 1):\n"
                "            status = '✅' if t['done'] else '⬜'\n"
                "            print(f'{i}. {status} {t[\"task\"]}')\n"
                "        print('\\n[A]dd  [D]one  [R]emove  [Q]uit')\n"
                "        choice = input('> ').strip().lower()\n"
                "        if choice == 'a':\n"
                "            task = input('Task: ')\n"
                "            todos.append({'task': task, 'done': False})\n"
                "        elif choice == 'd':\n"
                "            n = int(input('Mark done #: ')) - 1\n"
                "            if 0 <= n < len(todos): todos[n]['done'] = True\n"
                "        elif choice == 'r':\n"
                "            n = int(input('Remove #: ')) - 1\n"
                "            if 0 <= n < len(todos): todos.pop(n)\n"
                "        elif choice == 'q':\n"
                "            save_todos(todos)\n"
                "            print('Saved! Bye!')\n"
                "            break\n\n"
                "main()\n"
                "```"
            ),
            "web page html": (
                "📝 Basic Web Page:\n\n"
                "```html\n"
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>My Website</title>\n"
                "    <style>\n"
                "        * { margin: 0; padding: 0; box-sizing: border-box; }\n"
                "        body { font-family: Arial, sans-serif; }\n"
                "        header { background: #333; color: white; padding: 20px; text-align: center; }\n"
                "        nav { background: #555; padding: 10px; }\n"
                "        nav a { color: white; margin: 0 15px; text-decoration: none; }\n"
                "        main { max-width: 800px; margin: 20px auto; padding: 20px; }\n"
                "        footer { background: #333; color: white; text-align: center; padding: 10px; }\n"
                "    </style>\n"
                "</head>\n"
                "<body>\n"
                "    <header><h1>My Website</h1></header>\n"
                "    <nav>\n"
                "        <a href=\"#\">Home</a>\n"
                "        <a href=\"#\">About</a>\n"
                "        <a href=\"#\">Contact</a>\n"
                "    </nav>\n"
                "    <main>\n"
                "        <h2>Welcome!</h2>\n"
                "        <p>This is my website.</p>\n"
                "    </main>\n"
                "    <footer><p>&copy; 2025 My Website</p></footer>\n"
                "</body>\n"
                "</html>\n"
                "```"
            ),
            "selection sort": (
                "📝 Selection Sort in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "void selectionSort(int arr[], int n) {\n"
                "    for(int i = 0; i < n-1; i++) {\n"
                "        int minIdx = i;\n"
                "        for(int j = i+1; j < n; j++) {\n"
                "            if(arr[j] < arr[minIdx])\n"
                "                minIdx = j;\n"
                "        }\n"
                "        int temp = arr[i];\n"
                "        arr[i] = arr[minIdx];\n"
                "        arr[minIdx] = temp;\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {64, 25, 12, 22, 11};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    selectionSort(arr, n);\n"
                "    for(int i = 0; i < n; i++)\n"
                "        printf(\"%d \", arr[i]);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "insertion sort": (
                "📝 Insertion Sort in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "void insertionSort(int arr[], int n) {\n"
                "    for(int i = 1; i < n; i++) {\n"
                "        int key = arr[i];\n"
                "        int j = i - 1;\n"
                "        while(j >= 0 && arr[j] > key) {\n"
                "            arr[j+1] = arr[j];\n"
                "            j--;\n"
                "        }\n"
                "        arr[j+1] = key;\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {12, 11, 13, 5, 6};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    insertionSort(arr, n);\n"
                "    for(int i = 0; i < n; i++)\n"
                "        printf(\"%d \", arr[i]);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "merge sort": (
                "📝 Merge Sort in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "void merge(int arr[], int l, int m, int r) {\n"
                "    int n1 = m - l + 1, n2 = r - m;\n"
                "    int *L = malloc(n1 * sizeof(int));\n"
                "    int *R = malloc(n2 * sizeof(int));\n"
                "    for(int i = 0; i < n1; i++) L[i] = arr[l+i];\n"
                "    for(int j = 0; j < n2; j++) R[j] = arr[m+1+j];\n"
                "    int i=0, j=0, k=l;\n"
                "    while(i < n1 && j < n2)\n"
                "        arr[k++] = (L[i] <= R[j]) ? L[i++] : R[j++];\n"
                "    while(i < n1) arr[k++] = L[i++];\n"
                "    while(j < n2) arr[k++] = R[j++];\n"
                "    free(L); free(R);\n"
                "}\n\n"
                "void mergeSort(int arr[], int l, int r) {\n"
                "    if(l < r) {\n"
                "        int m = (l + r) / 2;\n"
                "        mergeSort(arr, l, m);\n"
                "        mergeSort(arr, m+1, r);\n"
                "        merge(arr, l, m, r);\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {38, 27, 43, 3, 9, 82, 10};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    mergeSort(arr, 0, n-1);\n"
                "    for(int i = 0; i < n; i++)\n"
                "        printf(\"%d \", arr[i]);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "quick sort": (
                "📝 Quick Sort in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "void swap(int *a, int *b) {\n"
                "    int t = *a; *a = *b; *b = t;\n"
                "}\n\n"
                "int partition(int arr[], int low, int high) {\n"
                "    int pivot = arr[high];\n"
                "    int i = low - 1;\n"
                "    for(int j = low; j < high; j++) {\n"
                "        if(arr[j] < pivot)\n"
                "            swap(&arr[++i], &arr[j]);\n"
                "    }\n"
                "    swap(&arr[i+1], &arr[high]);\n"
                "    return i + 1;\n"
                "}\n\n"
                "void quickSort(int arr[], int low, int high) {\n"
                "    if(low < high) {\n"
                "        int pi = partition(arr, low, high);\n"
                "        quickSort(arr, low, pi-1);\n"
                "        quickSort(arr, pi+1, high);\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int arr[] = {10, 7, 8, 9, 1, 5};\n"
                "    int n = sizeof(arr)/sizeof(arr[0]);\n"
                "    quickSort(arr, 0, n-1);\n"
                "    for(int i = 0; i < n; i++)\n"
                "        printf(\"%d \", arr[i]);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "binary tree": (
                "📝 Binary Tree in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "typedef struct Node {\n"
                "    int data;\n"
                "    struct Node *left, *right;\n"
                "} Node;\n\n"
                "Node* newNode(int val) {\n"
                "    Node *n = (Node*)malloc(sizeof(Node));\n"
                "    n->data = val;\n"
                "    n->left = n->right = NULL;\n"
                "    return n;\n"
                "}\n\n"
                "Node* insert(Node *root, int val) {\n"
                "    if(!root) return newNode(val);\n"
                "    if(val < root->data) root->left = insert(root->left, val);\n"
                "    else root->right = insert(root->right, val);\n"
                "    return root;\n"
                "}\n\n"
                "void inorder(Node *root) {\n"
                "    if(root) {\n"
                "        inorder(root->left);\n"
                "        printf(\"%d \", root->data);\n"
                "        inorder(root->right);\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    Node *root = NULL;\n"
                "    root = insert(root, 50);\n"
                "    insert(root, 30); insert(root, 70);\n"
                "    insert(root, 20); insert(root, 40);\n"
                "    printf(\"Inorder: \");\n"
                "    inorder(root);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "fibonacci": (
                "📝 Fibonacci in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "// Iterative (faster)\n"
                "void fibIterative(int n) {\n"
                "    int a = 0, b = 1;\n"
                "    for(int i = 0; i < n; i++) {\n"
                "        printf(\"%d \", a);\n"
                "        int temp = a + b;\n"
                "        a = b; b = temp;\n"
                "    }\n"
                "}\n\n"
                "// Recursive\n"
                "int fibRecursive(int n) {\n"
                "    if(n <= 1) return n;\n"
                "    return fibRecursive(n-1) + fibRecursive(n-2);\n"
                "}\n\n"
                "int main() {\n"
                "    printf(\"First 10 Fibonacci: \");\n"
                "    fibIterative(10);\n"
                "    printf(\"\\nfib(10) = %d\\n\", fibRecursive(10));\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "factorial": (
                "📝 Factorial in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n\n"
                "// Iterative\n"
                "long long factIterative(int n) {\n"
                "    long long result = 1;\n"
                "    for(int i = 2; i <= n; i++)\n"
                "        result *= i;\n"
                "    return result;\n"
                "}\n\n"
                "// Recursive\n"
                "long long factRecursive(int n) {\n"
                "    if(n <= 1) return 1;\n"
                "    return n * factRecursive(n-1);\n"
                "}\n\n"
                "int main() {\n"
                "    printf(\"5! = %lld\\n\", factIterative(5));\n"
                "    printf(\"10! = %lld\\n\", factRecursive(10));\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "palindrome": (
                "📝 Palindrome Check in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <string.h>\n"
                "#include <ctype.h>\n\n"
                "int isPalindrome(char *str) {\n"
                "    int left = 0, right = strlen(str) - 1;\n"
                "    while(left < right) {\n"
                "        while(left < right && !isalnum(str[left])) left++;\n"
                "        while(left < right && !isalnum(str[right])) right--;\n"
                "        if(tolower(str[left]) != tolower(str[right]))\n"
                "            return 0;\n"
                "        left++; right--;\n"
                "    }\n"
                "    return 1;\n"
                "}\n\n"
                "int main() {\n"
                "    char str[] = \"A man a plan a canal Panama\";\n"
                "    printf(\"\\\"%s\\\" is %sa palindrome\\n\",\n"
                "        str, isPalindrome(str) ? \"\" : \"not \");\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "reverse string": (
                "📝 Reverse String in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "void reverse(char *str) {\n"
                "    int left = 0, right = strlen(str) - 1;\n"
                "    while(left < right) {\n"
                "        char temp = str[left];\n"
                "        str[left] = str[right];\n"
                "        str[right] = temp;\n"
                "        left++; right--;\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    char str[] = \"Hello World\";\n"
                "    printf(\"Original: %s\\n\", str);\n"
                "    reverse(str);\n"
                "    printf(\"Reversed: %s\\n\", str);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "prime number": (
                "📝 Prime Number Check in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <math.h>\n\n"
                "int isPrime(int n) {\n"
                "    if(n < 2) return 0;\n"
                "    if(n < 4) return 1;\n"
                "    if(n % 2 == 0 || n % 3 == 0) return 0;\n"
                "    for(int i = 5; i <= sqrt(n); i += 6)\n"
                "        if(n % i == 0 || n % (i+2) == 0) return 0;\n"
                "    return 1;\n"
                "}\n\n"
                "int main() {\n"
                "    printf(\"Primes up to 50: \");\n"
                "    for(int i = 2; i <= 50; i++)\n"
                "        if(isPrime(i)) printf(\"%d \", i);\n"
                "    return 0;\n"
                "}\n"
                "```\n"
                "Compile with: gcc prime.c -o prime -lm"
            ),
            "matrix multiply": (
                "📝 Matrix Multiplication in C:\n\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#define N 3\n\n"
                "void multiply(int a[N][N], int b[N][N], int c[N][N]) {\n"
                "    for(int i = 0; i < N; i++)\n"
                "        for(int j = 0; j < N; j++) {\n"
                "            c[i][j] = 0;\n"
                "            for(int k = 0; k < N; k++)\n"
                "                c[i][j] += a[i][k] * b[k][j];\n"
                "        }\n"
                "}\n\n"
                "void print(int m[N][N]) {\n"
                "    for(int i = 0; i < N; i++) {\n"
                "        for(int j = 0; j < N; j++)\n"
                "            printf(\"%4d\", m[i][j]);\n"
                "        printf(\"\\n\");\n"
                "    }\n"
                "}\n\n"
                "int main() {\n"
                "    int a[N][N] = {{1,2,3},{4,5,6},{7,8,9}};\n"
                "    int b[N][N] = {{9,8,7},{6,5,4},{3,2,1}};\n"
                "    int c[N][N];\n"
                "    multiply(a, b, c);\n"
                "    print(c);\n"
                "    return 0;\n"
                "}\n"
                "```"
            ),
            "login system python": (
                "📝 Simple Login System in Python:\n\n"
                "```python\n"
                "import json, os, hashlib\n\n"
                "DB = 'users.json'\n\n"
                "def load_users():\n"
                "    if os.path.exists(DB):\n"
                "        with open(DB, 'r') as f: return json.load(f)\n"
                "    return {}\n\n"
                "def save_users(users):\n"
                "    with open(DB, 'w') as f: json.dump(users, f, indent=2)\n\n"
                "def hash_pw(pw):\n"
                "    return hashlib.sha256(pw.encode()).hexdigest()\n\n"
                "def register(users):\n"
                "    user = input('Username: ')\n"
                "    if user in users:\n"
                "        print('Username taken!'); return\n"
                "    pw = input('Password: ')\n"
                "    users[user] = hash_pw(pw)\n"
                "    save_users(users)\n"
                "    print('Registered!')\n\n"
                "def login(users):\n"
                "    user = input('Username: ')\n"
                "    pw = input('Password: ')\n"
                "    if user in users and users[user] == hash_pw(pw):\n"
                "        print(f'Welcome {user}!')\n"
                "    else:\n"
                "        print('Invalid credentials!')\n\n"
                "def main():\n"
                "    users = load_users()\n"
                "    while True:\n"
                "        print('\\n1. Register  2. Login  3. Quit')\n"
                "        c = input('> ')\n"
                "        if c == '1': register(users)\n"
                "        elif c == '2': login(users)\n"
                "        elif c == '3': break\n\n"
                "main()\n"
                "```"
            ),
        }
        
        # =============================================
        # CONCEPT EXPLANATIONS (Deep Knowledge)
        # =============================================
        self.concepts = {
            "pointer": (
                "📖 Pointers in C/C++:\n\n"
                "A pointer stores the memory address of another variable.\n\n"
                "Think of it like this:\n"
                "  📦 Variable = a box with a value inside\n"
                "  📍 Pointer = a note with the box's location\n\n"
                "Declaration:\n"
                "  int *ptr;           // pointer to int\n"
                "  char *cptr;         // pointer to char\n"
                "  void *vptr;         // generic pointer\n\n"
                "Usage:\n"
                "  int x = 10;\n"
                "  int *ptr = &x;      // & = address of x\n"
                "  printf(\"%d\", *ptr); // * = value at address (10)\n"
                "  *ptr = 20;          // changes x to 20!\n\n"
                "Key operators:\n"
                "  &  → \"address of\" operator\n"
                "  *  → \"dereference\" operator (get value)\n\n"
                "Common uses:\n"
                "  • Dynamic memory (malloc/new)\n"
                "  • Passing by reference to functions\n"
                "  • Arrays and strings\n"
                "  • Linked lists and trees\n\n"
                "⚠ Always initialize pointers!\n"
                "⚠ Check for NULL before using!"
            ),
            "array": (
                "📖 Arrays:\n\n"
                "An array is a collection of elements of the same type,\n"
                "stored in contiguous memory.\n\n"
                "C/C++ Arrays:\n"
                "  int arr[5] = {1, 2, 3, 4, 5};\n"
                "  arr[0] = 10;    // first element\n"
                "  arr[4] = 50;    // last element\n\n"
                "2D Array:\n"
                "  int grid[3][3] = {\n"
                "    {1, 2, 3},\n"
                "    {4, 5, 6},\n"
                "    {7, 8, 9}\n"
                "  };\n\n"
                "Python Lists (dynamic arrays):\n"
                "  arr = [1, 2, 3, 4, 5]\n"
                "  arr.append(6)    # add element\n"
                "  arr[0]           # access first\n\n"
                "Java:\n"
                "  int[] arr = {1, 2, 3, 4, 5};\n"
                "  int[] arr = new int[5];\n\n"
                "JavaScript:\n"
                "  let arr = [1, 2, 3, 4, 5];\n"
                "  arr.push(6);\n\n"
                "⚠ Array index starts at 0!\n"
                "⚠ C arrays have no bounds checking!"
            ),
            "string": (
                "📖 Strings:\n\n"
                "C Strings (char arrays):\n"
                "  char str[] = \"Hello\";\n"
                "  char str[50];\n"
                "  strcpy(str, \"Hello\");\n"
                "  strlen(str)           → 5\n"
                "  strcmp(s1, s2)         → 0 if equal\n"
                "  strcat(dest, src)      → concatenate\n"
                "  Need: #include <string.h>\n\n"
                "C++ Strings:\n"
                "  string s = \"Hello\";\n"
                "  s.length()   s.size()\n"
                "  s + \" World\"          → concatenate\n"
                "  s.substr(1, 3)        → \"ell\"\n"
                "  s.find(\"llo\")         → position\n"
                "  s[0]                  → 'H'\n"
                "  Need: #include <string>\n\n"
                "Python Strings:\n"
                "  s = \"Hello\"\n"
                "  len(s)    s.upper()    s.lower()\n"
                "  s.split()  s.strip()   s.replace()\n"
                "  f\"{name} is {age}\"   → f-string\n\n"
                "Java Strings:\n"
                "  String s = \"Hello\";\n"
                "  s.length()  s.charAt(0)  s.substring(1,3)\n"
                "  s.equals(other)  // NOT ==\n"
                "  s.toUpperCase()  s.toLowerCase()"
            ),
            "struct": (
                "📖 Structs (C/C++):\n\n"
                "A struct groups different data types together.\n"
                "Think of it as a custom data type.\n\n"
                "Definition:\n"
                "  struct Student {\n"
                "      char name[50];\n"
                "      int age;\n"
                "      float gpa;\n"
                "  };\n\n"
                "Usage:\n"
                "  struct Student s1;\n"
                "  strcpy(s1.name, \"John\");\n"
                "  s1.age = 20;\n"
                "  s1.gpa = 3.8;\n\n"
                "Initialize:\n"
                "  struct Student s2 = {\"Jane\", 22, 3.9};\n\n"
                "With typedef:\n"
                "  typedef struct {\n"
                "      int x, y;\n"
                "  } Point;\n"
                "  Point p = {10, 20};\n\n"
                "Pointer to struct:\n"
                "  struct Student *ptr = &s1;\n"
                "  ptr->age = 21;  // arrow operator\n"
                "  (*ptr).age = 21; // same thing"
            ),
            "class": (
                "📖 Classes:\n\n"
                "A class is a blueprint for creating objects.\n"
                "It combines data and functions together.\n\n"
                "C++ Class:\n"
                "  class Car {\n"
                "  private:\n"
                "      string brand;\n"
                "      int speed;\n"
                "  public:\n"
                "      Car(string b, int s) : brand(b), speed(s) {}\n"
                "      void drive() { cout << brand << \" driving!\"; }\n"
                "      string getBrand() { return brand; }\n"
                "  };\n"
                "  Car c(\"Toyota\", 120);\n"
                "  c.drive();\n\n"
                "Python Class:\n"
                "  class Car:\n"
                "      def __init__(self, brand, speed):\n"
                "          self.brand = brand\n"
                "          self.speed = speed\n"
                "      def drive(self):\n"
                "          print(f\"{self.brand} driving!\")\n"
                "  c = Car(\"Toyota\", 120)\n"
                "  c.drive()\n\n"
                "Java Class:\n"
                "  public class Car {\n"
                "      private String brand;\n"
                "      public Car(String b) { brand = b; }\n"
                "      public void drive() { System.out.println(brand); }\n"
                "  }"
            ),
            "loop": (
                "📖 Loops:\n\n"
                "Loops repeat code until a condition is met.\n\n"
                "FOR loop (known iterations):\n"
                "  C:  for(int i=0; i<10; i++) { }\n"
                "  Py: for i in range(10):\n"
                "  JS: for(let i=0; i<10; i++) { }\n\n"
                "WHILE loop (condition-based):\n"
                "  C:  while(x > 0) { x--; }\n"
                "  Py: while x > 0: x -= 1\n"
                "  JS: while(x > 0) { x--; }\n\n"
                "DO-WHILE (runs at least once):\n"
                "  C: do { scanf(\"%d\", &x); } while(x != 0);\n\n"
                "FOR-EACH (iterate collections):\n"
                "  C++: for(auto &item : vec) { }\n"
                "  Py:  for item in list:\n"
                "  JS:  arr.forEach(item => { });\n"
                "  Java: for(String s : list) { }\n\n"
                "Control:\n"
                "  break;     → exit loop\n"
                "  continue;  → skip to next iteration"
            ),
            "function": (
                "📖 Functions:\n\n"
                "Functions are reusable blocks of code.\n\n"
                "C/C++:\n"
                "  int add(int a, int b) {\n"
                "      return a + b;\n"
                "  }\n\n"
                "Python:\n"
                "  def add(a, b):\n"
                "      return a + b\n\n"
                "JavaScript:\n"
                "  function add(a, b) { return a + b; }\n"
                "  const add = (a, b) => a + b;\n\n"
                "Java:\n"
                "  public static int add(int a, int b) {\n"
                "      return a + b;\n"
                "  }\n\n"
                "PHP:\n"
                "  function add($a, $b) { return $a + $b; }\n\n"
                "Key concepts:\n"
                "  • Parameters → inputs\n"
                "  • Return value → output\n"
                "  • void → no return value\n"
                "  • Recursion → function calls itself"
            ),
            "recursion": (
                "📖 Recursion:\n\n"
                "A function that calls itself to solve a problem.\n\n"
                "Two requirements:\n"
                "  1. Base case → when to stop\n"
                "  2. Recursive case → breaks problem into smaller parts\n\n"
                "Factorial:\n"
                "  int factorial(int n) {\n"
                "      if(n <= 1) return 1;          // base case\n"
                "      return n * factorial(n - 1);    // recursive\n"
                "  }\n"
                "  // factorial(5) = 5 * 4 * 3 * 2 * 1 = 120\n\n"
                "Fibonacci:\n"
                "  int fib(int n) {\n"
                "      if(n <= 1) return n;\n"
                "      return fib(n-1) + fib(n-2);\n"
                "  }\n\n"
                "⚠ Always have a base case!\n"
                "⚠ Too deep = stack overflow\n"
                "💡 Can often be replaced with loops (iteration)"
            ),
            "oop": (
                "📖 Object-Oriented Programming (OOP):\n\n"
                "4 Pillars of OOP:\n\n"
                "1️⃣ ENCAPSULATION\n"
                "   Bundle data + methods together\n"
                "   Use private/public access control\n"
                "   class Box { private: int size; public: getSize(); }\n\n"
                "2️⃣ INHERITANCE\n"
                "   Create new class from existing one\n"
                "   Child inherits parent's properties\n"
                "   class Dog : public Animal { }\n\n"
                "3️⃣ POLYMORPHISM\n"
                "   Same interface, different behavior\n"
                "   virtual void speak() → overridden in subclass\n"
                "   Animal *a = new Dog(); a->speak(); // Woof!\n\n"
                "4️⃣ ABSTRACTION\n"
                "   Hide complex details, show simple interface\n"
                "   virtual void draw() = 0; // pure virtual\n\n"
                "Benefits:\n"
                "  ✅ Code reuse\n"
                "  ✅ Organized structure\n"
                "  ✅ Easy maintenance\n"
                "  ✅ Real-world modeling"
            ),
            "inheritance": (
                "📖 Inheritance:\n\n"
                "Create a new class based on existing one.\n"
                "Child class gets all properties of parent.\n\n"
                "C++:\n"
                "  class Animal {\n"
                "  public:\n"
                "      string name;\n"
                "      virtual void speak() { cout << \"...\"; }\n"
                "  };\n"
                "  class Dog : public Animal {\n"
                "  public:\n"
                "      void speak() override { cout << \"Woof!\"; }\n"
                "  };\n\n"
                "Python:\n"
                "  class Animal:\n"
                "      def speak(self): print('...')\n"
                "  class Dog(Animal):\n"
                "      def speak(self): print('Woof!')\n\n"
                "Java:\n"
                "  class Dog extends Animal {\n"
                "      void speak() { System.out.println(\"Woof!\"); }\n"
                "  }\n\n"
                "Types:\n"
                "  Single: A → B\n"
                "  Multi-level: A → B → C\n"
                "  Multiple: A,B → C (C++ only)"
            ),
            "malloc": (
                "📖 Dynamic Memory:\n\n"
                "Allocate memory at runtime (on the heap).\n\n"
                "C (malloc/free):\n"
                "  int *arr = (int*)malloc(n * sizeof(int));\n"
                "  if(!arr) { printf(\"Failed!\"); exit(1); }\n"
                "  // use arr...\n"
                "  free(arr); arr = NULL;\n\n"
                "C++ (new/delete):\n"
                "  int *arr = new int[n];\n"
                "  // use arr...\n"
                "  delete[] arr;\n\n"
                "C++ (smart pointers - preferred):\n"
                "  auto arr = make_unique<int[]>(n);\n"
                "  // auto-freed when out of scope!\n\n"
                "Python: Automatic! No manual memory management.\n"
                "Java: Automatic garbage collection.\n\n"
                "⚠ Every malloc → free\n"
                "⚠ Every new → delete\n"
                "⚠ Set pointer to NULL after free"
            ),
            "file": (
                "📖 File I/O:\n\n"
                "C:\n"
                "  FILE *fp = fopen(\"file.txt\", \"r\");\n"
                "  fgets(buf, sizeof(buf), fp);\n"
                "  fprintf(fp, \"text\");\n"
                "  fclose(fp);\n\n"
                "C++:\n"
                "  #include <fstream>\n"
                "  ofstream out(\"file.txt\");\n"
                "  out << \"Hello\";\n"
                "  ifstream in(\"file.txt\");\n"
                "  getline(in, line);\n\n"
                "Python:\n"
                "  with open('file.txt', 'r') as f:\n"
                "      content = f.read()\n"
                "  with open('file.txt', 'w') as f:\n"
                "      f.write('Hello')\n\n"
                "Java:\n"
                "  BufferedReader br = new BufferedReader(\n"
                "      new FileReader(\"file.txt\"));\n"
                "  String line = br.readLine();\n\n"
                "Modes: r(read) w(write) a(append) rb(binary)"
            ),
            "sort": (
                "📖 Sorting Algorithms:\n\n"
                "1. Bubble Sort - O(n²)\n"
                "   Compare adjacent, swap if needed\n"
                "   Simple but slow\n\n"
                "2. Selection Sort - O(n²)\n"
                "   Find minimum, place at front\n\n"
                "3. Insertion Sort - O(n²)\n"
                "   Insert each element in sorted position\n"
                "   Good for small/nearly sorted data\n\n"
                "4. Merge Sort - O(n log n)\n"
                "   Divide in half, sort each, merge\n"
                "   Stable, consistent performance\n\n"
                "5. Quick Sort - O(n log n) average\n"
                "   Pick pivot, partition around it\n"
                "   Fastest in practice\n\n"
                "Built-in:\n"
                "  C:   qsort(arr, n, sizeof(int), cmp);\n"
                "  C++: sort(v.begin(), v.end());\n"
                "  Py:  arr.sort() or sorted(arr)\n"
                "  JS:  arr.sort((a,b) => a-b);\n"
                "  Java: Arrays.sort(arr);"
            ),
            "data structure": (
                "📖 Data Structures Overview:\n\n"
                "Linear:\n"
                "  📦 Array      → fixed size, O(1) access\n"
                "  📦 Linked List → dynamic, O(1) insert/delete\n"
                "  📦 Stack      → LIFO (Last In First Out)\n"
                "  📦 Queue      → FIFO (First In First Out)\n\n"
                "Non-Linear:\n"
                "  🌳 Binary Tree    → hierarchical\n"
                "  🌳 BST            → sorted tree\n"
                "  🌳 Heap           → priority queue\n"
                "  🌳 Graph          → nodes + edges\n\n"
                "Hash-based:\n"
                "  #️⃣ Hash Table → O(1) average lookup\n"
                "  #️⃣ Hash Map  → key-value pairs\n\n"
                "Choosing the right one:\n"
                "  Need fast access by index? → Array\n"
                "  Need fast insert/delete?   → Linked List\n"
                "  Need LIFO?                 → Stack\n"
                "  Need FIFO?                 → Queue\n"
                "  Need fast search?           → BST / Hash\n"
                "  Need sorted data?           → BST / Sorted Array"
            ),
            "big o": (
                "📖 Big O Notation:\n\n"
                "Describes how algorithm performance scales.\n\n"
                "Common complexities (best → worst):\n\n"
                "  O(1)       → Constant    → Array access\n"
                "  O(log n)   → Logarithmic → Binary search\n"
                "  O(n)       → Linear      → Loop through array\n"
                "  O(n log n) → Linearithmic → Merge sort\n"
                "  O(n²)      → Quadratic   → Bubble sort\n"
                "  O(2^n)     → Exponential  → Recursive fib\n"
                "  O(n!)      → Factorial    → Permutations\n\n"
                "Examples:\n"
                "  O(1):     arr[5];\n"
                "  O(n):     for(i=0; i<n; i++)\n"
                "  O(n²):    for(i) for(j)\n"
                "  O(log n): while(n > 1) n /= 2;\n\n"
                "Rules:\n"
                "  • Drop constants: O(2n) → O(n)\n"
                "  • Drop smaller terms: O(n²+n) → O(n²)\n"
                "  • Worst case usually matters most"
            ),
            "git": (
                "📖 Git Basics:\n\n"
                "Setup:\n"
                "  git init                    → create repo\n"
                "  git clone <url>             → copy repo\n\n"
                "Daily workflow:\n"
                "  git status                  → check changes\n"
                "  git add .                   → stage all\n"
                "  git add file.c              → stage one file\n"
                "  git commit -m \"message\"     → commit\n"
                "  git push                    → push to remote\n"
                "  git pull                    → pull from remote\n\n"
                "Branching:\n"
                "  git branch                  → list branches\n"
                "  git branch feature          → create branch\n"
                "  git checkout feature        → switch branch\n"
                "  git checkout -b feature     → create + switch\n"
                "  git merge feature           → merge branch\n\n"
                "History:\n"
                "  git log                     → view history\n"
                "  git log --oneline           → compact view\n"
                "  git diff                    → see changes\n\n"
                "Undo:\n"
                "  git checkout -- file        → discard changes\n"
                "  git reset HEAD file         → unstage\n"
                "  git revert <commit>         → undo commit"
            ),
            "algorithm": (
                "📖 Common Algorithms:\n\n"
                "Searching:\n"
                "  🔍 Linear Search  → O(n) - check each element\n"
                "  🔍 Binary Search  → O(log n) - sorted array only\n\n"
                "Sorting:\n"
                "  📊 Bubble Sort    → O(n²) - simple\n"
                "  📊 Selection Sort → O(n²) - find min each pass\n"
                "  📊 Insertion Sort → O(n²) - good for small data\n"
                "  📊 Merge Sort     → O(n log n) - divide & conquer\n"
                "  📊 Quick Sort     → O(n log n) avg - fastest\n\n"
                "Graph:\n"
                "  🌐 BFS → Breadth-first (queue-based)\n"
                "  🌐 DFS → Depth-first (stack/recursion)\n"
                "  🌐 Dijkstra → shortest path\n\n"
                "Dynamic Programming:\n"
                "  📐 Break into subproblems\n"
                "  📐 Store results (memoization)\n"
                "  📐 Examples: Fibonacci, Knapsack, LCS"
            ),
            "design pattern": (
                "📖 Design Patterns:\n\n"
                "Creational:\n"
                "  🏗 Singleton  → one instance only\n"
                "  🏗 Factory    → create objects without specifying class\n"
                "  🏗 Builder    → step-by-step construction\n\n"
                "Structural:\n"
                "  🔧 Adapter   → convert interface\n"
                "  🔧 Decorator → add behavior dynamically\n"
                "  🔧 Facade    → simplified interface\n\n"
                "Behavioral:\n"
                "  📋 Observer  → notify on changes\n"
                "  📋 Strategy  → swappable algorithms\n"
                "  📋 Iterator  → traverse collection\n\n"
                "Singleton Example (C++):\n"
                "  class DB {\n"
                "    static DB* instance;\n"
                "    DB() {}\n"
                "  public:\n"
                "    static DB* get() {\n"
                "      if(!instance) instance = new DB();\n"
                "      return instance;\n"
                "    }\n"
                "  };"
            ),
            "difference": "Can you be more specific? For example:\n• 'difference between array and linked list'\n• 'difference between C and C++'\n• 'difference between stack and queue'",
            "difference between c and c++": (
                "📖 C vs C++:\n\n"
                "C:\n"
                "  • Procedural language\n"
                "  • No classes/objects\n"
                "  • Manual memory (malloc/free)\n"
                "  • printf/scanf for I/O\n"
                "  • .c extension\n"
                "  • Faster compilation\n\n"
                "C++:\n"
                "  • Object-oriented + procedural\n"
                "  • Classes, inheritance, polymorphism\n"
                "  • new/delete + smart pointers\n"
                "  • cin/cout for I/O\n"
                "  • STL (vector, map, etc.)\n"
                "  • .cpp extension\n"
                "  • Templates, exceptions, namespaces\n\n"
                "C++ is a superset of C (mostly).\n"
                "C is simpler, C++ is more powerful."
            ),
            "difference between stack and queue": (
                "📖 Stack vs Queue:\n\n"
                "Stack (LIFO - Last In First Out):\n"
                "  📚 Like a stack of plates\n"
                "  push(item)  → add to top\n"
                "  pop()       → remove from top\n"
                "  peek()      → look at top\n"
                "  Uses: undo, function calls, brackets matching\n\n"
                "Queue (FIFO - First In First Out):\n"
                "  🚶‍♂️ Like a line at a store\n"
                "  enqueue(item) → add to back\n"
                "  dequeue()     → remove from front\n"
                "  peek()        → look at front\n"
                "  Uses: scheduling, BFS, print queue"
            ),
            "difference between array and linked list": (
                "📖 Array vs Linked List:\n\n"
                "Array:\n"
                "  ✅ O(1) random access (arr[i])\n"
                "  ✅ Cache friendly (contiguous memory)\n"
                "  ❌ Fixed size (C) or expensive resize\n"
                "  ❌ O(n) insert/delete in middle\n\n"
                "Linked List:\n"
                "  ✅ O(1) insert/delete at head\n"
                "  ✅ Dynamic size\n"
                "  ❌ O(n) access (must traverse)\n"
                "  ❌ Extra memory for pointers\n"
                "  ❌ Not cache friendly\n\n"
                "Use Array when: frequent access by index\n"
                "Use Linked List when: frequent insert/delete"
            ),
            "difference between python and java": (
                "📖 Python vs Java:\n\n"
                "Python:\n"
                "  • Dynamically typed\n"
                "  • Interpreted (slower)\n"
                "  • Simple syntax\n"
                "  • Indentation-based blocks\n"
                "  • Great for scripting, data science, AI\n\n"
                "Java:\n"
                "  • Statically typed\n"
                "  • Compiled to bytecode (faster)\n"
                "  • Verbose syntax\n"
                "  • Curly brace blocks\n"
                "  • Great for enterprise, Android, web\n\n"
                "Python: x = 10\n"
                "Java:   int x = 10;\n\n"
                "Both are great choices!"
            ),
            "sql": (
                "📖 SQL (Structured Query Language):\n\n"
                "CREATE TABLE:\n"
                "  CREATE TABLE users (\n"
                "    id INT PRIMARY KEY AUTO_INCREMENT,\n"
                "    name VARCHAR(100),\n"
                "    email VARCHAR(100) UNIQUE,\n"
                "    age INT DEFAULT 0\n"
                "  );\n\n"
                "INSERT:\n"
                "  INSERT INTO users (name, email, age)\n"
                "  VALUES ('John', 'john@mail.com', 25);\n\n"
                "SELECT:\n"
                "  SELECT * FROM users;\n"
                "  SELECT name FROM users WHERE age > 20;\n"
                "  SELECT * FROM users ORDER BY name;\n"
                "  SELECT * FROM users LIMIT 10;\n\n"
                "UPDATE:\n"
                "  UPDATE users SET age = 26 WHERE id = 1;\n\n"
                "DELETE:\n"
                "  DELETE FROM users WHERE id = 1;\n\n"
                "JOIN:\n"
                "  SELECT u.name, o.total\n"
                "  FROM users u\n"
                "  JOIN orders o ON u.id = o.user_id;"
            ),
            "html": (
                "📖 HTML (HyperText Markup Language):\n\n"
                "Basic structure:\n"
                "  <!DOCTYPE html>\n"
                "  <html>\n"
                "  <head>\n"
                "    <title>Page Title</title>\n"
                "  </head>\n"
                "  <body>\n"
                "    <h1>Heading</h1>\n"
                "    <p>Paragraph</p>\n"
                "    <a href=\"url\">Link</a>\n"
                "    <img src=\"img.png\" alt=\"desc\">\n"
                "    <ul><li>Item</li></ul>\n"
                "    <div class=\"box\">Content</div>\n"
                "    <input type=\"text\" placeholder=\"Type...\">\n"
                "    <button>Click Me</button>\n"
                "  </body>\n"
                "  </html>\n\n"
                "Common tags:\n"
                "  h1-h6, p, a, img, div, span,\n"
                "  ul/ol/li, table/tr/td, form,\n"
                "  input, button, textarea, select"
            ),
            "css": (
                "📖 CSS (Cascading Style Sheets):\n\n"
                "Selectors:\n"
                "  element { }     →  p { color: red; }\n"
                "  .class { }     →  .box { padding: 10px; }\n"
                "  #id { }        →  #header { background: blue; }\n\n"
                "Box Model:\n"
                "  content → padding → border → margin\n\n"
                "Flexbox:\n"
                "  .container {\n"
                "    display: flex;\n"
                "    justify-content: center;\n"
                "    align-items: center;\n"
                "  }\n\n"
                "Grid:\n"
                "  .container {\n"
                "    display: grid;\n"
                "    grid-template-columns: 1fr 1fr 1fr;\n"
                "  }\n\n"
                "Common:\n"
                "  color, background, font-size,\n"
                "  padding, margin, border, width, height,\n"
                "  display, position, z-index"
            ),
            "javascript": (
                "📖 JavaScript:\n\n"
                "Variables:\n"
                "  let x = 10;\n"
                "  const PI = 3.14;\n\n"
                "Functions:\n"
                "  function greet(name) { return `Hello ${name}`; }\n"
                "  const greet = (name) => `Hello ${name}`;\n\n"
                "Arrays:\n"
                "  let arr = [1, 2, 3];\n"
                "  arr.push(4); arr.pop();\n"
                "  arr.map(x => x * 2);\n"
                "  arr.filter(x => x > 2);\n"
                "  arr.reduce((sum, x) => sum + x, 0);\n\n"
                "Objects:\n"
                "  let obj = { name: 'John', age: 25 };\n"
                "  obj.name; obj['age'];\n\n"
                "DOM:\n"
                "  document.getElementById('id')\n"
                "  document.querySelector('.class')\n"
                "  el.addEventListener('click', fn);"
            ),
            "php": (
                "📖 PHP:\n\n"
                "Variables:\n"
                "  $name = \"John\";\n"
                "  $age = 25;\n"
                "  $arr = [1, 2, 3];\n\n"
                "Print:\n"
                "  echo \"Hello World\";\n"
                "  echo \"Name: $name\";\n"
                "  print_r($arr);\n"
                "  var_dump($variable);\n\n"
                "Arrays:\n"
                "  $arr = [1, 2, 3];\n"
                "  $arr[] = 4;\n"
                "  array_push($arr, 5);\n"
                "  count($arr);\n"
                "  in_array(3, $arr);\n\n"
                "Associative:\n"
                "  $person = ['name' => 'John', 'age' => 25];\n"
                "  echo $person['name'];\n\n"
                "Functions:\n"
                "  function add($a, $b) { return $a + $b; }\n\n"
                "Form handling:\n"
                "  $name = $_POST['name'];\n"
                "  $id = $_GET['id'];\n"
                "  Always sanitize: htmlspecialchars($input)"
            ),
            "java": (
                "📖 Java:\n\n"
                "Hello World:\n"
                "  public class Main {\n"
                "    public static void main(String[] args) {\n"
                "      System.out.println(\"Hello World!\");\n"
                "    }\n"
                "  }\n\n"
                "Variables:\n"
                "  int x = 10;\n"
                "  double pi = 3.14;\n"
                "  String name = \"John\";\n"
                "  boolean flag = true;\n\n"
                "Arrays:\n"
                "  int[] arr = {1, 2, 3};\n"
                "  int[] arr = new int[5];\n\n"
                "ArrayList:\n"
                "  ArrayList<String> list = new ArrayList<>();\n"
                "  list.add(\"item\");\n"
                "  list.get(0);\n"
                "  list.size();\n\n"
                "Class:\n"
                "  public class Person {\n"
                "    private String name;\n"
                "    public Person(String n) { name = n; }\n"
                "    public String getName() { return name; }\n"
                "  }"
            ),
            "python": (
                "📖 Python:\n\n"
                "Variables:\n"
                "  x = 10\n"
                "  name = \"Hello\"\n"
                "  pi = 3.14\n"
                "  flag = True\n\n"
                "Print:\n"
                "  print(\"Hello\")\n"
                "  print(f\"Value: {x}\")\n\n"
                "Input:\n"
                "  name = input(\"Name: \")\n"
                "  age = int(input(\"Age: \"))\n\n"
                "Lists:\n"
                "  arr = [1, 2, 3]\n"
                "  arr.append(4)\n"
                "  arr.sort()\n"
                "  [x**2 for x in arr]  # list comprehension\n\n"
                "Dict:\n"
                "  d = {'name': 'John', 'age': 25}\n"
                "  d['name']\n\n"
                "Functions:\n"
                "  def add(a, b):\n"
                "      return a + b\n\n"
                "Classes:\n"
                "  class Dog:\n"
                "      def __init__(self, name):\n"
                "          self.name = name"
            ),
            "try catch": (
                "📖 Error Handling (try-catch):\n\n"
                "C++:\n"
                "  try {\n"
                "      throw runtime_error(\"Error!\");\n"
                "  } catch(exception &e) {\n"
                "      cout << e.what();\n"
                "  }\n\n"
                "Python:\n"
                "  try:\n"
                "      x = 1 / 0\n"
                "  except ZeroDivisionError as e:\n"
                "      print(f\"Error: {e}\")\n"
                "  finally:\n"
                "      print(\"Done\")\n\n"
                "Java:\n"
                "  try {\n"
                "      int x = 1 / 0;\n"
                "  } catch(ArithmeticException e) {\n"
                "      System.out.println(e.getMessage());\n"
                "  } finally {\n"
                "      System.out.println(\"Done\");\n"
                "  }\n\n"
                "JavaScript:\n"
                "  try {\n"
                "      throw new Error('Oops!');\n"
                "  } catch(e) {\n"
                "      console.error(e.message);\n"
                "  }"
            ),
            "segfault": (
                "🔧 Segmentation Fault:\n\n"
                "Your program tried to access memory it shouldn't.\n\n"
                "Common causes:\n"
                "  1. NULL pointer: int *p = NULL; *p = 10;\n"
                "  2. Array out of bounds: arr[100] when size is 5\n"
                "  3. Freed memory: free(p); *p = 10;\n"
                "  4. Stack overflow: infinite recursion\n"
                "  5. String literal: char *s = \"hi\"; s[0] = 'H';\n\n"
                "How to find it:\n"
                "  1. Add printf before suspicious lines\n"
                "  2. Compile with: gcc -g file.c\n"
                "  3. Run with: gdb ./a.out\n"
                "  4. Use valgrind: valgrind ./a.out\n\n"
                "Prevention:\n"
                "  ✅ Initialize all pointers\n"
                "  ✅ Check for NULL\n"
                "  ✅ Check array bounds\n"
                "  ✅ Free memory only once"
            ),
            "memory leak": (
                "🔧 Memory Leak:\n\n"
                "Allocated memory that's never freed.\n"
                "Program uses more and more RAM over time.\n\n"
                "Example:\n"
                "  void bad() {\n"
                "      int *p = malloc(sizeof(int));\n"
                "      // forgot free(p)! → LEAK\n"
                "  }\n\n"
                "Fix:\n"
                "  void good() {\n"
                "      int *p = malloc(sizeof(int));\n"
                "      *p = 42;\n"
                "      // ... use p ...\n"
                "      free(p);     // ✅ free when done\n"
                "      p = NULL;    // ✅ prevent dangling\n"
                "  }\n\n"
                "C++ solution → use smart pointers:\n"
                "  auto p = make_unique<int>(42);\n"
                "  // auto-freed!\n\n"
                "Detect: Use valgrind on Linux\n"
                "  valgrind --leak-check=full ./program"
            ),
            "undefined reference": (
                "🔧 Undefined Reference Error:\n\n"
                "The linker can't find a function/variable definition.\n\n"
                "Common causes:\n"
                "  1. Function declared but not defined\n"
                "     int add(int a, int b); // declared\n"
                "     // but never wrote the body!\n\n"
                "  2. Forgot to compile all files\n"
                "     gcc main.c utils.c -o program\n"
                "     // NOT just: gcc main.c\n\n"
                "  3. Missing library\n"
                "     gcc file.c -lm    // for math.h\n"
                "     gcc file.c -lpthread // for threads\n\n"
                "  4. Typo in function name\n"
                "     void myFunc() vs myfunction()\n\n"
                "  5. C++ name mangling\n"
                "     extern \"C\" { void cFunction(); }"
            ),
            "syntax error": (
                "🔧 Syntax Error:\n\n"
                "The code doesn't follow language rules.\n\n"
                "Common causes:\n"
                "  1. Missing semicolon\n"
                "     int x = 10   ← missing ;\n\n"
                "  2. Mismatched brackets\n"
                "     if(x > 0 {   ← missing )\n\n"
                "  3. Missing quotes\n"
                "     char *s = \"hello;  ← missing \"\n\n"
                "  4. Wrong keyword\n"
                "     fore(int i=0;...)  ← should be 'for'\n\n"
                "  5. Missing #include\n"
                "     Using printf without <stdio.h>\n\n"
                "How to fix:\n"
                "  1. Read the error message line number\n"
                "  2. Check THAT line AND the line BEFORE it\n"
                "  3. Look for missing ; ) } \"\n"
                "  4. Compile frequently to catch early"
            ),
            "indentation error": (
                "🔧 IndentationError (Python):\n\n"
                "Python uses indentation (spaces) for code blocks.\n\n"
                "Wrong:\n"
                "  if True:\n"
                "  print(\"Hello\")    ← needs indent!\n\n"
                "Right:\n"
                "  if True:\n"
                "      print(\"Hello\")  ← 4 spaces\n\n"
                "Common causes:\n"
                "  1. Mixing tabs and spaces\n"
                "  2. Inconsistent indentation\n"
                "  3. Missing indent after : (if, for, def, class)\n\n"
                "Fix:\n"
                "  • Use 4 spaces (not tabs)\n"
                "  • Configure editor: Tab = 4 spaces\n"
                "  • Be consistent throughout file"
            ),
            "null pointer": (
                "🔧 Null Pointer Exception:\n\n"
                "Trying to use a pointer/reference that is NULL/None/null.\n\n"
                "C/C++:\n"
                "  int *ptr = NULL;\n"
                "  *ptr = 10;  // CRASH!\n"
                "  Fix: if(ptr != NULL) { *ptr = 10; }\n\n"
                "Java:\n"
                "  String s = null;\n"
                "  s.length();  // NullPointerException!\n"
                "  Fix: if(s != null) { s.length(); }\n\n"
                "Python:\n"
                "  x = None\n"
                "  x.method()  // AttributeError!\n"
                "  Fix: if x is not None: x.method()\n\n"
                "JavaScript:\n"
                "  let obj = null;\n"
                "  obj.property  // TypeError!\n"
                "  Fix: if(obj) { obj.property; }\n"
                "  Better: obj?.property  // optional chaining"
            ),
            "compile": (
                "📖 How to Compile:\n\n"
                "In this editor:\n"
                "  1. Write code in the editor\n"
                "  2. Save file (Ctrl+S)\n"
                "  3. Click '▶ Compile' or press Ctrl+B\n"
                "  4. Check Output tab for results\n\n"
                "Command line:\n"
                "  C:   gcc file.c -o program\n"
                "  C++: g++ file.cpp -o program\n"
                "  With warnings: gcc -Wall -Wextra file.c\n"
                "  With debug: gcc -g file.c\n"
                "  C++17: g++ -std=c++17 file.cpp\n\n"
                "Other languages:\n"
                "  Python: python file.py (no compile needed)\n"
                "  Java:   javac Main.java && java Main\n"
                "  JS:     node file.js\n"
                "  PHP:    php file.php"
            ),
            "run": (
                "📖 How to Run:\n\n"
                "In this editor:\n"
                "  1. Save your file (Ctrl+S)\n"
                "  2. Click '▶ Run' or press Ctrl+R\n"
                "  3. Or use 'Build & Run' (F5)\n"
                "  4. Output appears in Output tab\n\n"
                "Keyboard shortcuts:\n"
                "  Ctrl+B → Compile\n"
                "  Ctrl+R → Run\n"
                "  F5     → Build & Run\n"
                "  Ctrl+S → Save\n"
                "  Ctrl+N → New file\n"
                "  Ctrl+O → Open file"
            ),
            "best practice": (
                "📖 Coding Best Practices:\n\n"
                "1. 📝 Use meaningful names\n"
                "   Bad:  int x, y, z;\n"
                "   Good: int width, height, depth;\n\n"
                "2. 💬 Write comments\n"
                "   // Calculate average of scores\n"
                "   float avg = total / count;\n\n"
                "3. 🔧 Keep functions small\n"
                "   Each function = one task\n"
                "   < 50 lines ideally\n\n"
                "4. 🚫 Don't repeat yourself (DRY)\n"
                "   Reuse code with functions\n\n"
                "5. ⚠ Handle errors\n"
                "   Check return values, use try-catch\n\n"
                "6. 📏 Consistent formatting\n"
                "   Same indent, same style throughout\n\n"
                "7. 🧪 Test your code\n"
                "   Test edge cases, empty input, large input\n\n"
                "8. 🔒 Initialize variables\n"
                "   Uninitialized = undefined behavior!"
            ),
            "naming convention": (
                "📖 Naming Conventions:\n\n"
                "C:\n"
                "  snake_case for functions/variables\n"
                "  UPPER_CASE for constants/macros\n"
                "  int max_value;\n"
                "  #define MAX_SIZE 100\n\n"
                "C++:\n"
                "  CamelCase for classes\n"
                "  camelCase for methods\n"
                "  class MyClass { void doSomething(); }\n\n"
                "Python:\n"
                "  snake_case for functions/variables\n"
                "  CamelCase for classes\n"
                "  UPPER_CASE for constants\n"
                "  def my_function():\n"
                "  class MyClass:\n\n"
                "Java:\n"
                "  CamelCase for classes\n"
                "  camelCase for methods/variables\n"
                "  public class MyClass {\n"
                "    private int myValue;\n"
                "    public void doSomething() { }\n"
                "  }\n\n"
                "JavaScript:\n"
                "  camelCase for variables/functions\n"
                "  CamelCase for classes\n"
                "  UPPER_CASE for constants"
            ),
            "linked list": (
                "📖 Linked List:\n\n"
                "A dynamic data structure where each node points to the next.\n\n"
                "Types:\n"
                "  • Singly Linked: A → B → C → NULL\n"
                "  • Doubly Linked: NULL ← A ↔ B ↔ C → NULL\n"
                "  • Circular: A → B → C → A\n\n"
                "Node structure:\n"
                "  struct Node {\n"
                "      int data;\n"
                "      struct Node *next;\n"
                "  };\n\n"
                "Operations:\n"
                "  Insert at head: O(1)\n"
                "  Insert at tail: O(n) or O(1) with tail pointer\n"
                "  Delete: O(n)\n"
                "  Search: O(n)\n\n"
                "Try: 'write linked list c' for full code!"
            ),
            "stack": (
                "📖 Stack (LIFO):\n\n"
                "Last In First Out — like a stack of plates.\n\n"
                "Operations:\n"
                "  push(item)  → add to top      O(1)\n"
                "  pop()       → remove from top  O(1)\n"
                "  peek/top()  → view top         O(1)\n"
                "  isEmpty()   → check if empty   O(1)\n\n"
                "Uses:\n"
                "  • Undo/Redo\n"
                "  • Function call stack\n"
                "  • Expression evaluation\n"
                "  • Bracket matching\n"
                "  • DFS traversal\n\n"
                "Try: 'write stack c' for full code!"
            ),
            "queue": (
                "📖 Queue (FIFO):\n\n"
                "First In First Out — like a line at a store.\n\n"
                "Operations:\n"
                "  enqueue(item) → add to back    O(1)\n"
                "  dequeue()     → remove front   O(1)\n"
                "  peek/front()  → view front     O(1)\n"
                "  isEmpty()     → check empty    O(1)\n\n"
                "Types:\n"
                "  • Simple Queue\n"
                "  • Circular Queue\n"
                "  • Priority Queue\n"
                "  • Deque (double-ended)\n\n"
                "Uses:\n"
                "  • Task scheduling\n"
                "  • BFS traversal\n"
                "  • Print queue\n"
                "  • Message queue\n\n"
                "Try: 'write queue c' for full code!"
            ),
            "hash": (
                "📖 Hash Table / Hash Map:\n\n"
                "Stores key-value pairs for fast lookup.\n\n"
                "How it works:\n"
                "  key → hash function → index → value\n\n"
                "Time complexity:\n"
                "  Insert: O(1) average\n"
                "  Search: O(1) average\n"
                "  Delete: O(1) average\n"
                "  Worst case: O(n) with collisions\n\n"
                "In different languages:\n"
                "  C++: unordered_map<string, int> m;\n"
                "       m[\"key\"] = 42;\n\n"
                "  Python: d = {'key': 42}\n"
                "          d['key']\n\n"
                "  Java: HashMap<String, Integer> m = new HashMap<>();\n"
                "        m.put(\"key\", 42);\n\n"
                "  JS: let m = new Map();\n"
                "      m.set('key', 42);"
            ),
            "graph": (
                "📖 Graphs:\n\n"
                "A collection of nodes (vertices) connected by edges.\n\n"
                "Types:\n"
                "  • Directed: A → B (one-way)\n"
                "  • Undirected: A — B (two-way)\n"
                "  • Weighted: edges have values\n\n"
                "Representations:\n"
                "  Adjacency Matrix: 2D array\n"
                "  Adjacency List: array of lists (preferred)\n\n"
                "Traversals:\n"
                "  BFS (Breadth-First): uses Queue\n"
                "  DFS (Depth-First): uses Stack/Recursion\n\n"
                "Algorithms:\n"
                "  • Dijkstra: shortest path\n"
                "  • Bellman-Ford: negative weights\n"
                "  • Kruskal/Prim: minimum spanning tree\n"
                "  • Topological Sort: ordering"
            ),
            "tree": (
                "📖 Trees:\n\n"
                "A hierarchical data structure with a root node.\n\n"
                "Binary Tree:\n"
                "  Each node has at most 2 children.\n"
                "        1\n"
                "       / \\\n"
                "      2   3\n"
                "     / \\\n"
                "    4   5\n\n"
                "Binary Search Tree (BST):\n"
                "  Left < Root < Right\n"
                "  Search: O(log n) average\n"
                "  Insert: O(log n) average\n\n"
                "Traversals:\n"
                "  Inorder (L-Root-R):   4 2 5 1 3\n"
                "  Preorder (Root-L-R):  1 2 4 5 3\n"
                "  Postorder (L-R-Root): 4 5 2 3 1\n"
                "  Level-order (BFS):    1 2 3 4 5\n\n"
                "Try: 'write binary tree' for full code!"
            ),
            "smart pointer": (
                "📖 Smart Pointers (C++):\n\n"
                "Automatic memory management — no manual delete!\n\n"
                "unique_ptr (exclusive ownership):\n"
                "  auto p = make_unique<int>(42);\n"
                "  auto arr = make_unique<int[]>(10);\n"
                "  // auto-freed when out of scope\n"
                "  // cannot copy, only move\n\n"
                "shared_ptr (shared ownership):\n"
                "  auto p = make_shared<int>(42);\n"
                "  auto p2 = p;  // both own it\n"
                "  // freed when last owner dies\n\n"
                "weak_ptr (non-owning):\n"
                "  weak_ptr<int> w = p;  // doesn't keep alive\n\n"
                "Rule of thumb:\n"
                "  • Use unique_ptr by default\n"
                "  • Use shared_ptr for shared ownership\n"
                "  • Avoid raw new/delete\n\n"
                "Need: #include <memory>"
            ),
            "template": (
                "📖 Templates (C++):\n\n"
                "Write code that works with any type.\n\n"
                "Function template:\n"
                "  template <typename T>\n"
                "  T maximum(T a, T b) {\n"
                "      return (a > b) ? a : b;\n"
                "  }\n"
                "  maximum(5, 3);        // int\n"
                "  maximum(3.14, 2.71);  // double\n\n"
                "Class template:\n"
                "  template <typename T>\n"
                "  class Stack {\n"
                "      vector<T> data;\n"
                "  public:\n"
                "      void push(T val) { data.push_back(val); }\n"
                "      T pop() { T v = data.back(); data.pop_back(); return v; }\n"
                "  };\n"
                "  Stack<int> s;\n"
                "  Stack<string> s2;\n\n"
                "STL uses templates extensively:\n"
                "  vector<int>, map<string,int>, etc."
            ),
            "vector": (
                "📖 Vector (C++ STL):\n\n"
                "Dynamic array that resizes automatically.\n\n"
                "  #include <vector>\n"
                "  vector<int> v;\n"
                "  vector<int> v = {1, 2, 3};\n"
                "  vector<int> v(10, 0); // 10 zeros\n\n"
                "Operations:\n"
                "  v.push_back(4);     // add to end\n"
                "  v.pop_back();       // remove last\n"
                "  v[0]                // access (no bounds check)\n"
                "  v.at(0)             // access (with bounds check)\n"
                "  v.size()            // current size\n"
                "  v.empty()           // is empty?\n"
                "  v.clear()           // remove all\n"
                "  v.front()           // first element\n"
                "  v.back()            // last element\n\n"
                "Iterate:\n"
                "  for(int x : v) cout << x;\n"
                "  for(int i=0; i<v.size(); i++) cout << v[i];\n\n"
                "Sort:\n"
                "  sort(v.begin(), v.end());"
            ),
            "map": (
                "📖 Map (C++ STL):\n\n"
                "Key-value pairs, sorted by key.\n\n"
                "  #include <map>\n"
                "  map<string, int> m;\n\n"
                "Operations:\n"
                "  m[\"apple\"] = 5;         // insert/update\n"
                "  m.insert({\"banana\", 3}); // insert\n"
                "  m[\"apple\"]              // access → 5\n"
                "  m.count(\"apple\")        // exists? → 1\n"
                "  m.erase(\"apple\");       // remove\n"
                "  m.size()                // count\n\n"
                "Iterate:\n"
                "  for(auto &[key, val] : m)\n"
                "      cout << key << \": \" << val;\n\n"
                "unordered_map → faster (O(1) vs O(log n))\n"
                "  #include <unordered_map>\n"
                "  unordered_map<string, int> m;"
            ),
            "lambda": (
                "📖 Lambda Functions:\n\n"
                "Anonymous functions — code without a name.\n\n"
                "C++:\n"
                "  auto add = [](int a, int b) { return a + b; };\n"
                "  add(3, 4); // 7\n\n"
                "  // With capture\n"
                "  int x = 10;\n"
                "  auto fn = [x]() { return x * 2; };\n"
                "  auto fn2 = [&x]() { x = 20; }; // by reference\n\n"
                "Python:\n"
                "  add = lambda a, b: a + b\n"
                "  add(3, 4)  # 7\n"
                "  sorted(list, key=lambda x: x[1])\n\n"
                "JavaScript:\n"
                "  const add = (a, b) => a + b;\n"
                "  arr.map(x => x * 2);\n"
                "  arr.filter(x => x > 5);\n\n"
                "Java:\n"
                "  (a, b) -> a + b\n"
                "  list.forEach(item -> System.out.println(item));"
            ),
            "exception": (
                "📖 Exceptions:\n\n"
                "Handle runtime errors gracefully.\n\n"
                "C++:\n"
                "  try {\n"
                "      if(x == 0) throw runtime_error(\"Zero!\");\n"
                "      result = 10 / x;\n"
                "  } catch(const exception &e) {\n"
                "      cerr << e.what() << endl;\n"
                "  }\n\n"
                "Python:\n"
                "  try:\n"
                "      result = 10 / x\n"
                "  except ZeroDivisionError:\n"
                "      print(\"Cannot divide by zero!\")\n"
                "  except Exception as e:\n"
                "      print(f\"Error: {e}\")\n"
                "  finally:\n"
                "      print(\"Always runs\")\n\n"
                "Java:\n"
                "  try { } \n"
                "  catch(Exception e) { e.getMessage(); }\n"
                "  finally { }\n\n"
                "Best practices:\n"
                "  • Catch specific exceptions first\n"
                "  • Don't catch everything blindly\n"
                "  • Use finally for cleanup"
            ),
            "regex": (
                "📖 Regular Expressions:\n\n"
                "Pattern matching for strings.\n\n"
                "Common patterns:\n"
                "  .     → any character\n"
                "  \\d    → digit [0-9]\n"
                "  \\w    → word char [a-zA-Z0-9_]\n"
                "  \\s    → whitespace\n"
                "  *     → 0 or more\n"
                "  +     → 1 or more\n"
                "  ?     → 0 or 1\n"
                "  ^     → start of string\n"
                "  $     → end of string\n"
                "  [abc]  → a or b or c\n"
                "  (abc)  → group\n"
                "  |      → or\n\n"
                "Examples:\n"
                "  Email: ^[\\w.-]+@[\\w.-]+\\.\\w+$\n"
                "  Phone: ^\\d{3}-\\d{3}-\\d{4}$\n"
                "  URL: ^https?://[\\w.-]+(\\.[\\w.-]+)+[/#?]?.*$\n\n"
                "In code:\n"
                "  C++: regex re(\"pattern\"); regex_match(s, re);\n"
                "  Python: import re; re.match(r\"pattern\", s)\n"
                "  Java: Pattern p = Pattern.compile(\"pattern\"); p.matcher(s).matches();\n"
                "  JS: let re = /pattern/; re.test(s);"
            )
        }
        
        # =============================================
        # ERROR DIAGNOSIS PATTERNS
        # =============================================
        self.error_patterns = {
            "expected": "This usually means something is missing before this point.\nCheck for missing semicolons, brackets, or parentheses on the previous line.",
            "undeclared": "The variable or function hasn't been declared.\nMake sure you:\n1. Declared it before using it\n2. Spelled it correctly\n3. Included the right header file",
            "implicit declaration": "You're using a function without declaring it.\nAdd the proper #include at the top:\n  #include <stdio.h> for printf/scanf\n  #include <string.h> for strcpy/strlen\n  #include <stdlib.h> for malloc/free",
            "incompatible type": "You're trying to assign or pass a value of the wrong type.\nCheck:\n1. Variable types match\n2. Function parameter types\n3. Return type matches",
            "redefinition": "You've defined the same variable/function twice.\nCheck:\n1. Duplicate function definitions\n2. Variable declared twice in same scope\n3. Missing include guards in headers",
            "no such file": "The file or header can't be found.\nCheck:\n1. File name spelling\n2. File exists in the right directory\n3. Include path is correct",
            "linker error": "The compiler found the declaration but not the definition.\nCheck:\n1. Compile ALL source files together\n2. Function has a body, not just declaration\n3. Library is linked (-lm, -lpthread)",
            "stack overflow": "Too much memory used on the stack.\nCommon causes:\n1. Infinite recursion (missing base case)\n2. Very large local arrays\n3. Too deep recursion\nFix: Add/fix base case, or use heap (malloc)",
            "floating point": "Issue with decimal number operations.\nCommon causes:\n1. Division by zero\n2. Precision issues (0.1 + 0.2 != 0.3)\n3. Overflow (number too large)\nFix: Check for zero before dividing",
            "permission denied": "The program can't access a file/resource.\nCheck:\n1. File permissions\n2. File is not open elsewhere\n3. Run as administrator if needed",
            "timeout": "The program took too long to finish.\nCommon causes:\n1. Infinite loop\n2. Very inefficient algorithm\n3. Waiting for input that never comes\nFix: Check loop conditions, optimize algorithm",
            "index out of": "Accessing an array/list beyond its size.\nFix:\n1. Check array size before accessing\n2. Loop condition: i < size (not i <= size)\n3. Remember: index starts at 0!",
            "division by zero": "Trying to divide by zero.\nFix:\n  if(b != 0) {\n      result = a / b;\n  } else {\n      printf(\"Error: cannot divide by zero!\");\n  }",
            "cannot find symbol": "Java: The compiler can't find what you're referencing.\nCheck:\n1. Spelling and capitalization\n2. Import statements\n3. Variable is in scope\n4. Method exists in the class",
            "modulenotfounderror": "Python: The module isn't installed.\nFix:\n  pip install module_name\n  pip3 install module_name\n\nOr check spelling:\n  import os  ← correct\n  import Os  ← wrong (case sensitive)",
            "typeerror": "Python: Wrong type used in an operation.\nExamples:\n  '5' + 3     → TypeError (string + int)\n  Fix: int('5') + 3\n  \n  len(5)      → TypeError (int has no len)\n  Fix: len(str(5))\n\nCheck your variable types with type(var)",
            "nameerror": "Python: Variable/function not defined.\nCommon causes:\n1. Typo in variable name\n2. Variable used before assignment\n3. Function called before definition\n4. Forgot to import module",
            "keyerror": "Python: Dictionary key doesn't exist.\nFix:\n  Use .get() with default:\n    value = d.get('key', 'default')\n  \n  Or check first:\n    if 'key' in d:\n        value = d['key']",
            "valueerror": "Python: Right type but wrong value.\nExamples:\n  int('hello')  → ValueError\n  int('3.14')   → ValueError\n\nFix:\n  try:\n      x = int(input('Number: '))\n  except ValueError:\n      print('Not a valid number!')",
            "attributeerror": "Python: Object doesn't have that attribute/method.\nCommon causes:\n1. Typo in method name\n2. Wrong variable type\n3. None value: x = None; x.method()\n\nFix: Check type with type(var) and dir(var)",
            "importerror": "Python: Can't import the module.\nFix:\n1. pip install module_name\n2. Check spelling\n3. Check Python version compatibility\n4. Check if file name conflicts with module name",
            "indexerror": "Python: List index out of range.\nFix:\n  if index < len(my_list):\n      value = my_list[index]\n\nRemember: index starts at 0!\n  list of 5 items → valid indices: 0,1,2,3,4",
            "filenotfounderror": "Python: File doesn't exist at that path.\nFix:\n  import os\n  if os.path.exists('file.txt'):\n      with open('file.txt') as f:\n          data = f.read()\n\nCheck:\n1. File name spelling\n2. Correct directory\n3. Use absolute path if unsure",
            "syntaxerror": "Python: Invalid syntax.\nCommon causes:\n1. Missing colon after if/for/def/class\n2. Mismatched quotes or brackets\n3. Using = instead of == in condition\n4. Missing parentheses in print (Python 3)\n\nCheck the line BEFORE the error too!",
            "recursionerror": "Python: Maximum recursion depth exceeded.\nYour recursive function has no proper base case.\n\nFix:\n1. Add/fix base case\n2. Increase limit: import sys; sys.setrecursionlimit(10000)\n3. Convert to iterative solution",
            "zerodivisionerror": "Python: Division by zero.\nFix:\n  if divisor != 0:\n      result = number / divisor\n  else:\n      print('Cannot divide by zero!')",
            "overflowerror": "Number too large to handle.\nFix:\n1. Use appropriate data type\n2. Check calculations for overflow\n3. Python: use // for integer division\n4. C: use long long instead of int",
            "warning": "Warnings don't stop compilation but indicate potential issues.\nCommon:\n  -Wunused-variable: variable declared but not used\n  -Wreturn-type: function missing return statement\n  -Wimplicit: function used without declaration\n\nFix warnings — they often reveal real bugs!",
            "core dump": "Program crashed and dumped memory state.\nSame as segfault — check:\n1. NULL pointer access\n2. Array out of bounds\n3. Use after free\n4. Stack overflow\n\nDebug: gcc -g file.c && gdb ./a.out",
        }

        # =============================================
        # SMART QUESTION PATTERNS
        # =============================================
        self.question_patterns = {
            "how to": self._handle_how_to,
            "how do i": self._handle_how_to,
            "how can i": self._handle_how_to,
            "what is": self._handle_what_is,
            "what are": self._handle_what_is,
            "what does": self._handle_what_does,
            "why": self._handle_why,
            "when": self._handle_when,
            "can you": self._handle_can_you,
            "write": self._handle_write,
            "create": self._handle_write,
            "make": self._handle_write,
            "build": self._handle_write,
            "show me": self._handle_write,
            "give me": self._handle_write,
            "explain": self._handle_explain,
            "teach me": self._handle_explain,
            "tell me about": self._handle_explain,
            "fix": self._handle_fix,
            "solve": self._handle_fix,
            "debug": self._handle_fix,
            "convert": self._handle_convert,
            "translate": self._handle_convert,
            "compare": self._handle_compare,
            "difference": self._handle_compare,
        }

    # =============================================
    # HELPER METHODS
    # =============================================
    def _get_capabilities(self):
        return (
            "🤖 Here's what I can do:\n\n"
            "💬 CHAT:\n"
            "  • Answer coding questions\n"
            "  • Explain concepts in simple terms\n"
            "  • Remember our conversation\n"
            "  • Learn from our chats\n\n"
            "📝 CODE:\n"
            "  • Write code snippets (C, C++, Python, Java, JS, PHP)\n"
            "  • Analyze your code for issues\n"
            "  • Suggest improvements\n"
            "  • Generate templates (calculator, linked list, etc.)\n\n"
            "🔧 DEBUG:\n"
            "  • Explain error messages\n"
            "  • Find common bugs\n"
            "  • Suggest fixes\n\n"
            "📚 TEACH:\n"
            "  • Data structures & algorithms\n"
            "  • OOP concepts\n"
            "  • Design patterns\n"
            "  • Best practices\n\n"
            "💡 Try:\n"
            "  'write a calculator in python'\n"
            "  'explain pointers'\n"
            "  'what is OOP'\n"
            "  'how to sort an array'"
        )

    def _handle_how_to(self, topic):
        """Handle 'how to...' questions"""
        topic_lower = topic.lower()

        how_to_responses = {
            "sort": "To sort:\n\nC++: sort(v.begin(), v.end());\nPython: arr.sort() or sorted(arr)\nJS: arr.sort((a,b) => a-b)\nJava: Arrays.sort(arr)\n\nWant a specific sorting algorithm? Ask me!\nTry: 'bubble sort', 'merge sort', 'quick sort'",
            "reverse": "To reverse:\n\nC++: reverse(v.begin(), v.end());\nPython: arr.reverse() or arr[::-1]\nJS: arr.reverse()\nJava: Collections.reverse(list)\n\nReverse a string? Try: 'reverse string'",
            "read file": "See my 'file' topic for file I/O in all languages!\nTry asking: 'explain file' or 'file read write c'",
            "write file": "See my 'file' topic for file I/O in all languages!\nTry asking: 'explain file' or 'file read write c'",
            "create array": "See my 'array' topic!\nTry asking: 'explain array'",
            "use pointer": "See my 'pointer' topic!\nTry asking: 'explain pointer'",
            "make class": "See my 'class' topic!\nTry asking: 'explain class'",
            "install": "Installation depends on what you need:\n\nPython package: pip install package_name\nNode.js package: npm install package\nC compiler: Install MinGW (Windows) or gcc (Linux)\nJava: Install JDK from oracle.com\n\nWhat are you trying to install?",
            "compile": "To compile in this editor:\n1. Save file (Ctrl+S)\n2. Click Compile (Ctrl+B)\n3. Check Output tab\n\nCommand line:\n  C: gcc file.c -o program\n  C++: g++ file.cpp -o program",
            "debug": "Debugging tips:\n1. Read error messages carefully\n2. Add print statements\n3. Check line numbers in errors\n4. Use a debugger (gdb, pdb)\n5. Test with simple inputs first\n6. Rubber duck debugging — explain your code out loud!",
            "learn programming": "Great question! Here's a roadmap:\n\n1. Start with Python (easiest)\n2. Learn variables, loops, functions\n3. Practice with small projects\n4. Learn data structures\n5. Try C/C++ for deeper understanding\n6. Build projects!\n\nWhat language interests you?",
            "learn c": "C Learning Path:\n1. Hello World & printf\n2. Variables & data types\n3. If-else & loops\n4. Functions\n5. Arrays & strings\n6. Pointers\n7. Structs\n8. File I/O\n9. Dynamic memory\n10. Data structures\n\nStart with 'hello world c'!",
            "learn python": "Python Learning Path:\n1. print() & variables\n2. input() & type conversion\n3. if-elif-else\n4. for & while loops\n5. Functions\n6. Lists & dictionaries\n7. Classes\n8. File I/O\n9. Modules\n10. Projects!\n\nStart with 'hello world python'!",
            "learn java": "Java Learning Path:\n1. Hello World & System.out.println\n2. Variables & data types\n3. If-else & loops\n4. Methods\n5. Arrays & ArrayList\n6. Classes & Objects\n7. Inheritance & Interfaces\n8. Exception handling\n9. File I/O\n10. Collections\n\nStart with 'hello world java'!",
            "learn javascript": "JavaScript Learning Path:\n1. console.log & variables\n2. Data types & operators\n3. If-else & loops\n4. Functions & arrow functions\n5. Arrays & Objects\n6. DOM manipulation\n7. Events\n8. Async/Await & Promises\n9. Fetch API\n10. Frameworks (React, Vue)\n\nStart with 'hello world javascript'!",
            "center a div": "The age-old question! 😄\n\nFlexbox (easiest):\n  .parent {\n    display: flex;\n    justify-content: center;\n    align-items: center;\n    height: 100vh;\n  }\n\nGrid:\n  .parent {\n    display: grid;\n    place-items: center;\n    height: 100vh;\n  }",
            "print": "Printing in different languages:\n\nC:      printf(\"Hello %s, age %d\\n\", name, age);\nC++:    cout << \"Hello \" << name << endl;\nPython: print(f\"Hello {name}, age {age}\")\nJava:   System.out.println(\"Hello \" + name);\nJS:     console.log(`Hello ${name}`);\nPHP:    echo \"Hello $name\";",
            "input": "Getting user input:\n\nC:      scanf(\"%d\", &x); or fgets(str, size, stdin);\nC++:    cin >> x; or getline(cin, str);\nPython: x = input(\"Enter: \")\n        num = int(input(\"Number: \"))\nJava:   Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine();\n        int n = sc.nextInt();\nJS:     prompt(\"Enter:\") // browser",
            "loop": "See my 'loop' topic!\nTry: 'explain loop'",
            "use git": "See my 'git' topic!\nTry: 'explain git'",
            "use malloc": "See my 'malloc' topic!\nTry: 'explain malloc'",
            "handle error": "See my 'try catch' topic!\nTry: 'explain try catch' or 'explain exception'",
            "use vector": "See my 'vector' topic!\nTry: 'explain vector'",
            "use map": "See my 'map' topic!\nTry: 'explain map'",
            "use template": "See my 'template' topic!\nTry: 'explain template'",
            "pass by reference": "Passing by reference allows a function to modify the original variable.\n\nC (using pointers):\n  void increment(int *x) { (*x)++; }\n  int a = 5;\n  increment(&a); // a is now 6\n\nC++ (using references):\n  void increment(int &x) { x++; }\n  int a = 5;\n  increment(a); // a is now 6\n\nPython: Lists/dicts are passed by reference automatically.\nJava: Objects are passed by reference, primitives by value.",
            "return multiple values": "Returning multiple values:\n\nC (using pointers):\n  void minmax(int *arr, int n, int *min, int *max) {\n      *min = *max = arr[0];\n      for(int i=1; i<n; i++) {\n          if(arr[i] < *min) *min = arr[i];\n          if(arr[i] > *max) *max = arr[i];\n      }\n  }\n\nC++ (using struct or pair):\n  pair<int,int> minmax(vector<int> &v);\n  auto [mn, mx] = minmax(v); // C++17\n\nPython (tuples):\n  def minmax(arr):\n      return min(arr), max(arr)\n  mn, mx = minmax(arr)",
        }

        for key, response in how_to_responses.items():
            if key in topic_lower:
                return response

        # Check concepts
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        # Check code templates
        for key, response in self.code_templates.items():
            key_words = set(key.split())
            topic_words = set(topic_lower.split())
            if len(key_words & topic_words) >= 1:
                return response

        return f"How to {topic}:\n\nI'll try to help! Can you be more specific?\nFor example:\n• Which programming language?\n• What exactly are you trying to achieve?\n• Any code you've tried so far?\n\nPaste your code in the editor and I can analyze it!"

    def _handle_what_is(self, topic):
        """Handle 'what is...' questions"""
        topic_lower = topic.lower().strip("? ")

        # Check concepts first
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        what_is = {
            "api": "API (Application Programming Interface) is a set of rules that lets programs talk to each other.\n\nExample: A weather app uses a weather API to get data.\n\nREST API:\n  GET    /users      → get all users\n  GET    /users/1    → get user 1\n  POST   /users      → create user\n  PUT    /users/1    → update user 1\n  DELETE /users/1    → delete user 1",
            "ide": "IDE (Integrated Development Environment) is a software tool for writing code.\n\nFeatures:\n• Code editor with syntax highlighting\n• Compiler/interpreter\n• Debugger\n• File management\n\nPopular IDEs:\n• VS Code (multi-language)\n• Visual Studio (C/C++/C#)\n• PyCharm (Python)\n• IntelliJ (Java)\n• This editor! 😊",
            "compiler": "A compiler translates source code into machine code.\n\nSource code (.c) → Compiler → Machine code (.exe)\n\nCompilers:\n• GCC (C/C++) - most common\n• Clang (C/C++) - modern\n• MSVC (Windows C/C++)\n• javac (Java → bytecode)\n\nInterpreters (no compilation):\n• Python, JavaScript, PHP, Ruby",
            "variable": "A variable is a named storage for data.\n\nC:      int age = 25;\nPython: age = 25\nJava:   int age = 25;\nJS:     let age = 25;\n\nTypes:\n• Integer (int) → whole numbers\n• Float/Double → decimals\n• String → text\n• Boolean → true/false\n• Char → single character",
            "framework": "A framework is a pre-built structure for building software.\n\nWeb frameworks:\n• Django (Python)\n• Flask (Python)\n• Express (Node.js)\n• React (JavaScript)\n• Spring (Java)\n• Laravel (PHP)\n\nA framework gives you:\n• Project structure\n• Common functionality\n• Best practices\n• Faster development",
            "database": "A database stores organized data.\n\nRelational (SQL):\n• MySQL, PostgreSQL, SQLite\n• Tables with rows and columns\n• Use SQL to query\n\nNoSQL:\n• MongoDB (documents)\n• Redis (key-value)\n• Firebase (real-time)\n\nBasic SQL:\n  SELECT * FROM users WHERE age > 20;",
            "recursion": self.concepts.get("recursion", "Recursion is when a function calls itself."),
            "algorithm": self.concepts.get("algorithm", "An algorithm is a step-by-step procedure."),
            "oop": self.concepts.get("oop", "OOP is Object-Oriented Programming."),
            "null": "NULL / None / null:\n\nA special value meaning 'no value' or 'nothing'.\n\nC/C++: NULL or nullptr\n  int *ptr = NULL;\n\nPython: None\n  x = None\n\nJava: null\n  String s = null;\n\nJavaScript: null and undefined\n  let x = null;      // intentionally empty\n  let y = undefined; // not yet assigned\n\n⚠ Always check before using!",
            "boolean": "Boolean = true or false.\n\nC: (no built-in, use 0/1 or #include <stdbool.h>)\n  bool flag = true;\n\nC++: bool flag = true;\nPython: flag = True\nJava: boolean flag = true;\nJS: let flag = true;\n\nUsed in conditions:\n  if(flag) { /* do something */ }",
            "library": "A library is pre-written code you can use.\n\nC Standard Library:\n  stdio.h, stdlib.h, string.h, math.h\n\nC++ STL:\n  vector, map, set, algorithm, string\n\nPython:\n  os, sys, json, math, datetime, re\n  pip install → third party libraries\n\nJava:\n  java.util, java.io, java.net\n\nJS/Node:\n  npm install → thousands of packages",
            "debugging": "Debugging is finding and fixing bugs in code.\n\nTechniques:\n1. 🖨 Print statements (printf/print/console.log)\n2. 🔍 Read error messages carefully\n3. 🐛 Use a debugger (gdb, pdb, IDE debugger)\n4. 🦆 Rubber duck debugging\n5. 🧪 Test with simple inputs\n6. 📖 Check documentation\n7. 🔄 Binary search the bug (comment out half)",
            "scope": "Scope defines where a variable is accessible.\n\nLocal scope:\n  void func() {\n      int x = 10; // only inside func()\n  }\n\nGlobal scope:\n  int x = 10; // accessible everywhere\n\nBlock scope:\n  if(true) {\n      int y = 5; // only inside this block\n  }\n\nPython: local, enclosing, global, built-in (LEGB)\nJS: var (function scope), let/const (block scope)",
            "type casting": "Type casting converts one data type to another.\n\nC:\n  int x = (int)3.14;        // explicit cast → 3\n  double d = 5;             // implicit cast → 5.0\n  int *p = (int*)malloc(4); // void* to int*\n\nC++:\n  static_cast<int>(3.14)\n  dynamic_cast<Derived*>(basePtr)\n\nPython:\n  int('5')   str(42)   float('3.14')\n  list('abc') → ['a','b','c']\n\nJava:\n  (int)3.14   Integer.parseInt(\"5\")\n  String.valueOf(42)",
            "reference": "References in C++:\n\nA reference is an alias for another variable.\n\n  int x = 10;\n  int &ref = x;  // ref IS x\n  ref = 20;      // x is now 20!\n\nFunction parameters:\n  void swap(int &a, int &b) {\n      int temp = a; a = b; b = temp;\n  }\n  swap(x, y); // actually swaps!\n\nDifference from pointer:\n  • Reference can't be NULL\n  • Reference can't be reassigned\n  • No need for * or & to use\n  • Must be initialized",
        }

        for key, response in what_is.items():
            if key in topic_lower:
                return response

        return f"📖 '{topic.strip()}' — That's an interesting topic!\n\nI don't have a specific entry for that yet, but I'm learning!\n\nCan you tell me more about what aspect you want to know?\nOr try related topics like:\n• Data structures\n• Algorithms\n• Specific language features\n• Programming concepts"

    def _handle_what_does(self, topic):
        """Handle 'what does X do' questions"""
        topic_lower = topic.lower()

        operators = {
            "++": "++ is the increment operator.\n  x++ → post-increment (use then add 1)\n  ++x → pre-increment (add 1 then use)\n\n  int x = 5;\n  printf(\"%d\", x++); // prints 5, x becomes 6\n  printf(\"%d\", ++x); // x becomes 7, prints 7",
            "--": "-- is the decrement operator.\n  x-- → post-decrement\n  --x → pre-decrement\n\n  int x = 5;\n  x--; // x is now 4",
            "+=": "+= adds and assigns.\n  x += 5; is same as x = x + 5;\n\n  Similar: -=, *=, /=, %=, &=, |=, ^=",
            "&&": "&& is logical AND.\n  if(a > 0 && b > 0) // true only if BOTH are true",
            "||": "|| is logical OR.\n  if(a > 0 || b > 0) // true if EITHER is true",
            "!": "! is logical NOT.\n  if(!done) // true if done is false",
            "==": "== compares for equality.\n  if(x == 5) // true if x is 5\n\n⚠ Don't confuse with = (assignment)!\n  x = 5  → assigns 5 to x\n  x == 5 → checks if x is 5",
            "!=": "!= means 'not equal'.\n  if(x != 0) // true if x is not zero",
            "->": "-> is the arrow operator for pointers to structs.\n  struct Node *ptr;\n  ptr->data = 10;  // same as (*ptr).data = 10;",
            "::": ":: is the scope resolution operator in C++.\n  std::cout → cout from std namespace\n  MyClass::method() → method of MyClass",
            "<<": "<< is either:\n1. Left shift: x << 2 (multiply by 4)\n2. Output in C++: cout << \"Hello\"",
            ">>": ">> is either:\n1. Right shift: x >> 2 (divide by 4)\n2. Input in C++: cin >> x",
            "&": "& has two uses:\n1. Address-of: int *ptr = &x; (get address)\n2. Bitwise AND: result = a & b;",
            "*": "* has multiple uses:\n1. Multiplication: 5 * 3\n2. Pointer declaration: int *ptr;\n3. Dereference: value = *ptr;\n4. In Python: unpacking *args",
            "sizeof": "sizeof returns the size in bytes.\n  sizeof(int)     → 4 (usually)\n  sizeof(char)    → 1\n  sizeof(double)  → 8\n  sizeof(arr)     → total bytes of array\n  sizeof(arr)/sizeof(arr[0]) → array length",
            "typedef": "typedef creates an alias for a type.\n  typedef unsigned long ulong;\n  ulong x = 42;\n\n  typedef struct {\n      int x, y;\n  } Point;\n  Point p = {10, 20};",
            "#define": "#define creates a macro/constant.\n  #define PI 3.14159\n  #define MAX(a,b) ((a)>(b)?(a):(b))\n  #define SQUARE(x) ((x)*(x))\n\n⚠ No semicolon at the end!\n⚠ Use parentheses around parameters!",
            "return": "return exits a function and gives back a value.\n  int add(int a, int b) {\n      return a + b;\n  }\n\n  void print() {\n      printf(\"Hello\");\n      return;  // optional for void\n  }",
            "void": "void means 'no type' or 'nothing'.\n  void func() → function returns nothing\n  void *ptr → generic pointer (any type)\n  (void)x → suppress unused variable warning",
            "static": "static has different meanings:\n\n1. Static variable (keeps value between calls):\n  void count() {\n      static int n = 0;\n      n++; // n persists!\n  }\n\n2. Static in class (shared by all objects):\n  class Counter {\n      static int count;\n  };\n\n3. Static function (file scope only):\n  static void helper() { } // only in this file",
            "const": "const means the value cannot change.\n\nC/C++:\n  const int MAX = 100;\n  const char *str = \"hello\";\n  void func(const int *ptr); // won't modify *ptr\n\nJavaScript:\n  const PI = 3.14;\n  const arr = [1,2]; // can modify array contents!\n  arr.push(3); // OK\n  arr = []; // ERROR",
            "extern": "extern declares a variable/function defined elsewhere.\n\nUsed for sharing between files:\n\nfile1.c:\n  int count = 0;  // definition\n\nfile2.c:\n  extern int count;  // declaration (uses file1's count)\n  count++;",
            "volatile": "volatile tells the compiler the value can change unexpectedly.\n\nUsed for:\n• Hardware registers\n• Variables modified by interrupt handlers\n• Shared variables in multithreading\n\n  volatile int sensor_value;\n  // Compiler won't optimize reads away",
            "auto": "auto lets the compiler deduce the type automatically.\n\nC++11:\n  auto x = 10;           // int\n  auto pi = 3.14;        // double\n  auto name = \"Hello\"s;  // string\n  auto it = vec.begin(); // iterator\n\n  for(auto &item : vec) { } // range-based for",
        }

        for key, response in operators.items():
            if key in topic_lower:
                return response

        # Check concepts
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        return f"I'll explain what '{topic.strip()}' does.\nCan you provide more context? Like:\n• Which language?\n• Show me the line of code\n• What's the full statement?"

    def _handle_why(self, topic):
        """Handle 'why...' questions"""
        topic_lower = topic.lower()

        why_answers = {
            "semicolon": "Semicolons (;) mark the end of a statement in C/C++/Java/JS.\nThe compiler needs to know where one statement ends.\n\nPython doesn't need them — it uses line breaks instead.",
            "main": "main() is the entry point of C/C++ programs.\nThe OS calls main() when you run your program.\n  int main() → returns 0 for success\n  int main(int argc, char *argv[]) → with command line args",
            "include": "#include copies the contents of a header file into your code.\nHeaders contain function declarations needed by the compiler.\n  #include <stdio.h> → tells compiler about printf, scanf, etc.",
            "header": "Header files (.h) contain declarations (not definitions).\nThey tell the compiler what functions/types exist.\nThe actual code is in .c/.cpp files or libraries.",
            "return 0": "return 0 in main() tells the OS the program ran successfully.\n  0 = success\n  non-zero = error\nThe OS can check this to know if your program failed.",
            "pointer": "Pointers exist because:\n1. Dynamic memory allocation\n2. Passing large data efficiently\n3. Building data structures (linked lists, trees)\n4. Direct hardware access\n5. Arrays are basically pointers!",
            "error": "Errors happen! Common reasons:\n1. Typos in code\n2. Logic mistakes\n3. Wrong types\n4. Missing files\n5. Null pointers\n\nShare the error and I'll help diagnose it!",
            "crash": "Programs crash due to:\n1. Segfault (bad memory access)\n2. Stack overflow (infinite recursion)\n3. Division by zero\n4. Null pointer dereference\n5. Out of memory\n\nShare the error for specific help!",
            "slow": "Code can be slow because:\n1. Inefficient algorithm (O(n²) vs O(n))\n2. Too many nested loops\n3. Unnecessary memory allocation\n4. I/O bottleneck\n5. Not using proper data structures\n\nPaste your code and I'll analyze it!",
            "use linux": "Linux is popular for programming because:\n1. Free and open source\n2. Built-in compilers (gcc, g++)\n3. Powerful terminal\n4. Package managers (apt, yum)\n5. Most servers run Linux\n6. Better for development tools",
            "use class": "Classes help because:\n1. Group related data and behavior\n2. Code reuse through inheritance\n3. Encapsulation (hide details)\n4. Model real-world objects\n5. Make large programs manageable",
            "use function": "Functions help because:\n1. Code reuse (DRY principle)\n2. Break big problems into small ones\n3. Easier to test and debug\n4. Better readability\n5. Reduce code duplication",
            "not working": "Let's figure out why! To help you I need:\n1. What error message are you getting?\n2. What did you expect to happen?\n3. What actually happened?\n4. Paste your code in the editor\n\nI'll analyze it for you!",
            "learning": "Learning programming is worth it because:\n1. 💰 Great career opportunities\n2. 🧠 Develops problem-solving skills\n3. 🏗 Build anything you imagine\n4. 🌍 Work from anywhere\n5. 🤖 Shape the future of technology",
        }

        for key, response in why_answers.items():
            if key in topic_lower:
                return response

        return f"Good question! Why {topic.strip()}?\n\nI'd be happy to explain the reasoning. Can you give me a bit more context about what specifically you want to understand?"

    def _handle_when(self, topic):
        """Handle 'when...' questions"""
        topic_lower = topic.lower()

        when_answers = {
            "pointer": "Use pointers when:\n• Dynamic memory allocation needed\n• Passing large data to functions\n• Building linked data structures\n• Working with arrays\n• Need to modify function parameters",
            "class": "Use classes when:\n• Grouping related data and behavior\n• Need multiple instances\n• Want inheritance/polymorphism\n• Building large applications\n• Modeling real-world objects",
            "struct": "Use structs when:\n• Need to group different data types\n• Simple data container (no complex behavior)\n• C language (no classes available)\n• Performance-critical (default public in C++)",
            "array": "Use arrays when:\n• Need fast access by index O(1)\n• Size is known/fixed\n• Need contiguous memory\n• Working with matrices",
            "linked list": "Use linked lists when:\n• Frequent insertions/deletions\n• Size changes often\n• Don't need random access\n• Memory is fragmented",
            "recursion": "Use recursion when:\n• Problem has recursive nature (trees, fractals)\n• Divide and conquer (merge sort, binary search)\n• Code is cleaner than iteration\n\nUse iteration when:\n• Performance matters\n• Deep recursion possible",
            "malloc": "Use dynamic memory when:\n• Size not known at compile time\n• Need memory to outlive function\n• Large data (too big for stack)\n• Building flexible data structures",
            "vector": "Use vector when:\n• Need dynamic array (size changes)\n• Want automatic memory management\n• Need fast random access\n• Working with C++ STL algorithms",
            "map": "Use map/dictionary when:\n• Need key-value pairs\n• Need fast lookup by key\n• Need to count occurrences\n• Building caches or indexes",
            "template": "Use templates when:\n• Same logic works for multiple types\n• Want type-safe generic code\n• Building reusable libraries\n• Example: sort works for int, float, string, etc.",
        }

        for key, response in when_answers.items():
            if key in topic_lower:
                return response

        return f"When to use {topic.strip()}:\n\nCould you be more specific? I can explain when to use:\n• Data structures\n• Design patterns\n• Specific language features\n• Programming concepts"

    def _handle_can_you(self, topic):
        """Handle 'can you...' questions"""
        topic_lower = topic.lower()

        if any(w in topic_lower for w in ["write", "create", "make", "build", "code", "generate"]):
            return self._handle_write(topic)
        if any(w in topic_lower for w in ["explain", "teach", "tell"]):
            return self._handle_explain(topic)
        if any(w in topic_lower for w in ["fix", "debug", "solve", "help"]):
            return self._handle_fix(topic)

        return "Yes, I can try! 💪 What exactly do you need? Be specific and I'll do my best!"

    def _handle_write(self, topic):
        """Handle 'write/create/make...' requests"""
        topic_lower = topic.lower()

        # Check code templates - improved matching
        best_template = None
        best_score = 0

        for key, code in self.code_templates.items():
            key_words = set(key.split())
            topic_words = set(topic_lower.split())
            score = len(key_words & topic_words)

            # Bonus for exact substring match
            if key in topic_lower:
                score += 3

            if score > best_score and score >= 2:
                best_score = score
                best_template = code

        if best_template:
            return best_template

        # Single keyword match for templates
        for key, code in self.code_templates.items():
            key_words = key.split()
            for kw in key_words:
                if len(kw) > 3 and kw in topic_lower:
                    return code

        # Detect language and generate appropriate response
        if "python" in topic_lower or "py" in topic_lower:
            lang = "Python"
        elif "java" in topic_lower and "script" not in topic_lower:
            lang = "Java"
        elif "javascript" in topic_lower or "js" in topic_lower:
            lang = "JavaScript"
        elif "php" in topic_lower:
            lang = "PHP"
        elif "c++" in topic_lower or "cpp" in topic_lower:
            lang = "C++"
        elif " c " in topic_lower or topic_lower.startswith("c ") or "in c" in topic_lower:
            lang = "C"
        elif "html" in topic_lower:
            lang = "HTML"
        elif "sql" in topic_lower:
            lang = "SQL"
        else:
            lang = None

        if lang:
            return (
                f"I'd love to write that in {lang}! 📝\n\n"
                f"To give you the best code, can you tell me:\n"
                f"1. What exactly should it do?\n"
                f"2. Any specific requirements?\n"
                f"3. Input/output format?\n\n"
                f"Meanwhile, try these specific requests:\n"
                f"• 'hello world {lang.lower()}'\n"
                f"• 'calculator {lang.lower()}'\n"
                f"• 'linked list c'\n"
                f"• 'bubble sort'\n"
                f"• 'binary search'\n"
                f"• 'binary tree'\n"
                f"• 'fibonacci'\n"
                f"• 'todo list python'\n"
                f"• 'login system python'"
            )

        return (
            "I can write code for you! 📝\n\n"
            "Please specify:\n"
            "1. Programming language (C, C++, Python, Java, JS, PHP)\n"
            "2. What should the code do?\n\n"
            "Example requests:\n"
            "• 'write a calculator in C'\n"
            "• 'create a linked list in C'\n"
            "• 'make a todo list in Python'\n"
            "• 'write hello world in Java'\n"
            "• 'create a web page in HTML'\n"
            "• 'write binary tree'\n"
            "• 'write merge sort'\n"
            "• 'write login system python'"
        )

    def _handle_explain(self, topic):
        """Handle 'explain...' requests"""
        topic_lower = topic.lower()

        # Check concepts
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        # Check code templates
        for key, response in self.code_templates.items():
            if key in topic_lower:
                return response

        # Check error patterns
        for key, response in self.error_patterns.items():
            if key in topic_lower:
                return f"🔧 {key}:\n\n{response}"

        return (
            f"I'd like to explain '{topic.strip()}'! 📚\n\n"
            f"I have detailed explanations for:\n"
            f"• pointer, array, string, struct, class\n"
            f"• loop, function, recursion, OOP\n"
            f"• inheritance, malloc, file, sort\n"
            f"• data structure, big O, algorithm\n"
            f"• design pattern, git, regex\n"
            f"• vector, map, template, lambda\n"
            f"• smart pointer, exception, hash\n"
            f"• stack, queue, linked list, tree, graph\n"
            f"• Python, Java, JavaScript, PHP, SQL, HTML, CSS\n\n"
            f"Try: 'explain [topic]'"
        )

    def _handle_fix(self, topic):
        """Handle 'fix/debug/solve...' requests"""
        topic_lower = topic.lower()

        # Check error patterns
        for key, response in self.error_patterns.items():
            if key in topic_lower:
                return f"🔧 Error: {key}\n\n{response}"

        # Check concepts for error-related topics
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        return (
            "🔧 I'll help you fix it!\n\n"
            "To debug effectively, please share:\n"
            "1. The error message (exact text)\n"
            "2. Paste your code in the editor\n"
            "3. What were you trying to do?\n\n"
            "I can diagnose:\n"
            "• Segfaults, memory leaks, core dumps\n"
            "• Syntax errors, type errors\n"
            "• Logic bugs\n"
            "• Runtime crashes\n"
            "• Python/Java/JS errors too!\n\n"
            "Common errors I know:\n"
            "  segfault, memory leak, syntax error,\n"
            "  null pointer, undefined reference,\n"
            "  TypeError, NameError, ValueError,\n"
            "  IndexError, KeyError, ImportError\n\n"
            "Tip: Paste code in editor, then ask me about the error!"
        )

    def _handle_convert(self, topic):
        """Handle conversion requests"""
        topic_lower = topic.lower()

        # Check if specific languages mentioned
        languages = {
            "c ": "C", "c++": "C++", "cpp": "C++",
            "python": "Python", "java": "Java",
            "javascript": "JavaScript", "js": "JavaScript",
            "php": "PHP"
        }

        found_langs = []
        for key, lang in languages.items():
            if key in topic_lower:
                found_langs.append(lang)

        if len(found_langs) >= 2:
            return (
                f"🔄 Converting {found_langs[0]} to {found_langs[1]}:\n\n"
                f"Please paste your {found_langs[0]} code in the editor,\n"
                f"then I'll help you convert it to {found_langs[1]}!\n\n"
                f"Or ask me for specific examples:\n"
                f"• 'hello world {found_langs[1].lower()}'\n"
                f"• 'calculator {found_langs[1].lower()}'\n\n"
                f"I can show you the same concept in different languages."
            )

        return (
            "🔄 Code conversion help:\n\n"
            "I can help convert between languages!\n"
            "Tell me:\n"
            "1. From which language?\n"
            "2. To which language?\n"
            "3. Paste the code in the editor\n\n"
            "I know: C, C++, Python, Java, JavaScript, PHP\n\n"
            "Example: 'convert this C code to Python'\n"
            "(with code in the editor)"
        )

    def _handle_compare(self, topic):
        """Handle comparison requests"""
        topic_lower = topic.lower()

        # Check concepts for "difference between" entries
        for key, response in self.concepts.items():
            if key in topic_lower:
                return response

        return (
            "📊 I can compare things for you!\n\n"
            "Try asking:\n"
            "• 'difference between C and C++'\n"
            "• 'difference between array and linked list'\n"
            "• 'difference between stack and queue'\n"
            "• 'difference between Python and Java'\n"
            "• 'compare for and while loop'"
        )
        
    # =============================================
    # MAIN RESPONSE ENGINE (SINGLE VERSION - FIXED)
    # =============================================
    def _find_response(self, message, code=""):
        """Ultra-smart response finder - FIXED version with proper priority"""
        msg_lower = message.strip().lower()
        msg_words = set(msg_lower.split())

        # Track context
        self._update_context(msg_lower, code)

        # 1. Check greetings FIRST (highest priority for short messages)
        clean_msg = msg_lower.strip().rstrip('!?., ')
        for key, response in self.greetings.items():
            if clean_msg == key or clean_msg == key + '!' or clean_msg == key + '.':
                return response
            if msg_lower.startswith(key) and len(msg_lower) < len(key) + 5:
                return response

        # 2. Check social/emotional responses
        for key, response in self.social.items():
            if key in msg_lower:
                return response

        # 3. Check question patterns (how to, what is, etc.)
        for pattern, handler in self.question_patterns.items():
            if msg_lower.startswith(pattern):
                # Extract topic by removing pattern
                topic = msg_lower
                for p in sorted(self.question_patterns.keys(), key=len, reverse=True):
                    if topic.startswith(p):
                        topic = topic[len(p):].strip()
                        break
                result = handler(topic if topic else msg_lower)
                if result:
                    return result

        # Also check if pattern appears inside message
        for pattern, handler in self.question_patterns.items():
            if f" {pattern} " in f" {msg_lower} " and not msg_lower.startswith(pattern):
                topic = msg_lower
                for p in sorted(self.question_patterns.keys(), key=len, reverse=True):
                    topic = topic.replace(p, "").strip()
                result = handler(topic if topic else msg_lower)
                if result:
                    return result

        # 4. Check code templates (exact or close match)
        best_template = None
        best_template_score = 0
        for key, response in self.code_templates.items():
            key_words = set(key.split())
            score = len(key_words & msg_words)
            # Bonus for substring match
            if key in msg_lower:
                score += 3
            if score > best_template_score and score >= 2:
                best_template_score = score
                best_template = response

        if best_template:
            return best_template

        # 5. Check concepts (with smart scoring)
        best_concept = None
        best_concept_score = 0
        for key, response in self.concepts.items():
            key_words = set(key.split())
            score = len(key_words & msg_words)
            # Bonus for exact substring
            if key in msg_lower:
                score += 3
            # Bonus for key being a significant part of message
            if len(key) > 3 and key in msg_lower:
                score += 2
            if score > best_concept_score and score >= 1:
                best_concept_score = score
                best_concept = response

        if best_concept and best_concept_score >= 2:
            return best_concept

        # 6. Check error patterns
        for key, response in self.error_patterns.items():
            if key in msg_lower:
                return f"🔧 Error Help: {key}\n\n{response}"

        # 7. Check if user shared code → analyze it
        if code.strip() and len(code.strip()) > 20:
            if any(w in msg_lower for w in [
                "check", "review", "analyze", "look", "see", "wrong",
                "issue", "bug", "problem", "fix", "help", "error",
                "what", "why", "how", "run", "compile", "work",
                "correct", "improve", "suggest", "opinion"
            ]):
                return self._analyze_code(message, code)

        # 8. Single keyword concept match (lower priority)
        if best_concept and best_concept_score >= 1:
            return best_concept

        # 9. Check code templates with single keyword
        for key, response in self.code_templates.items():
            key_words = key.split()
            for kw in key_words:
                if len(kw) > 3 and kw in msg_lower:
                    return response

        # 10. Check if message contains code-like content
        if any(w in msg_lower for w in ["code", "program", "script", "function", "variable"]):
            return self._handle_write(msg_lower)

        # 11. Follow-up from context
        if self.context.get("topic") and len(msg_lower.split()) <= 4:
            combined = f"{self.context['topic']} {msg_lower}"
            for key, response in self.concepts.items():
                if key in combined:
                    return f"📖 Continuing on {self.context['topic']}:\n\n{response}"
            for key, response in self.code_templates.items():
                if key in combined:
                    return response

        # 12. Code analysis if code present but no specific question
        if code.strip() and len(code.strip()) > 20:
            return self._analyze_code(message, code)

        # 13. Check knowledge base (learned responses) - MOVED TO LOWER PRIORITY
        kb_result = self.knowledge.search(msg_lower)
        if kb_result and len(kb_result) > 50:
            # Only use KB if it's a substantial response
            # And not a generic fallback
            if "I'm not sure" not in kb_result and "I understood" not in kb_result:
                return kb_result

        # 14. Teach mode
        if any(w in msg_lower for w in ["learn", "study", "understand", "beginner", "start", "tutorial"]):
            return (
                "📚 Great! Let's learn together!\n\n"
                "What would you like to learn?\n\n"
                "🟢 Beginner:\n"
                "  • 'teach me python'\n"
                "  • 'teach me C'\n"
                "  • 'what is a variable'\n"
                "  • 'hello world python'\n\n"
                "🟡 Intermediate:\n"
                "  • 'explain pointers'\n"
                "  • 'explain OOP'\n"
                "  • 'how to use classes'\n"
                "  • 'write linked list c'\n\n"
                "🔴 Advanced:\n"
                "  • 'explain design patterns'\n"
                "  • 'explain big O'\n"
                "  • 'explain smart pointers'\n"
                "  • 'write merge sort'\n\n"
                "Pick a topic and let's dive in!"
            )

        # 15. Generic smart response (last resort)
        return (
            f"🤔 I understood: \"{message}\"\n\n"
            f"I'm not sure about the exact answer, but I can help if you:\n\n"
            f"📝 Ask about coding topics:\n"
            f"  'explain pointers'\n"
            f"  'what is OOP'\n"
            f"  'how to sort an array'\n\n"
            f"💻 Request code:\n"
            f"  'write hello world in C'\n"
            f"  'create a calculator in python'\n"
            f"  'write binary tree'\n\n"
            f"🔧 Get debugging help:\n"
            f"  'fix segfault'\n"
            f"  'why am I getting syntax error'\n\n"
            f"📋 Paste code in the editor and ask:\n"
            f"  'check my code'\n"
            f"  'what's wrong with my code'\n\n"
            f"💡 Topics I know well:\n"
            f"  pointer, array, string, struct, class, loop,\n"
            f"  function, recursion, OOP, inheritance, sort,\n"
            f"  linked list, stack, queue, tree, graph,\n"
            f"  vector, map, template, smart pointer,\n"
            f"  big O, design pattern, git, regex,\n"
            f"  C, C++, Python, Java, JS, PHP, SQL, HTML, CSS\n\n"
            f"I learn from our conversations — teach me something new! 🧠"
        )

    def _update_context(self, msg_lower, code):
        """Track conversation context"""
        # Detect language from message
        lang_map = {
            "python": "Python", "py ": "Python",
            "javascript": "JavaScript", " js ": "JavaScript",
            "php": "PHP", "sql": "SQL",
            "html": "HTML", "css": "CSS",
            "c++": "C++", "cpp": "C++",
        }

        for key, lang in lang_map.items():
            if key in msg_lower:
                self.context["language"] = lang
                break

        # Special handling for "C" to avoid false matches
        if " c " in msg_lower or msg_lower.startswith("c ") or msg_lower.endswith(" c"):
            if "c++" not in msg_lower and "cpp" not in msg_lower:
                self.context["language"] = "C"

        # Java (but not JavaScript)
        if "java" in msg_lower and "script" not in msg_lower:
            self.context["language"] = "Java"

        # Detect from code
        if code.strip():
            self.context["code_shared"] = True
            if "#include" in code:
                if "iostream" in code or "cout" in code or "class " in code:
                    self.context["language"] = "C++"
                else:
                    self.context["language"] = "C"
            elif "def " in code and ("import " in code or "print(" in code):
                self.context["language"] = "Python"
            elif "public static void main" in code:
                self.context["language"] = "Java"
            elif "<?php" in code:
                self.context["language"] = "PHP"
            elif "function " in code or "const " in code or "let " in code:
                self.context["language"] = "JavaScript"
            elif "<html" in code.lower() or "<!DOCTYPE" in code:
                self.context["language"] = "HTML"
            elif "SELECT" in code or "CREATE TABLE" in code:
                self.context["language"] = "SQL"

        # Detect topic
        topics = [
            "pointer", "array", "string", "struct", "class", "loop",
            "function", "recursion", "sort", "search", "file", "oop",
            "inheritance", "template", "vector", "map", "stack", "queue",
            "tree", "graph", "linked list", "malloc", "memory", "hash",
            "lambda", "exception", "regex", "smart pointer", "design pattern",
            "big o", "algorithm", "data structure", "git", "variable",
            "compile", "debug", "error"
        ]
        for t in topics:
            if t in msg_lower:
                self.context["topic"] = t
                break

        # Detect mood
        if any(w in msg_lower for w in ["error", "bug", "wrong", "fail", "crash", "help", "stuck", "broken", "not working"]):
            self.context["mood"] = "frustrated"
            self.context["error_mode"] = True
        elif any(w in msg_lower for w in ["thanks", "great", "awesome", "cool", "nice", "perfect", "works", "solved"]):
            self.context["mood"] = "happy"
            self.context["error_mode"] = False
        elif any(w in msg_lower for w in ["learn", "teach", "explain", "understand", "how", "what", "why"]):
            self.context["mood"] = "curious"
            self.context["teach_mode"] = True

        # Track question
        self.context["last_question"] = msg_lower

    # =============================================
    # CODE ANALYSIS (SINGLE VERSION - FIXED)
    # =============================================
    def _analyze_code(self, message, code):
        """Deep code analysis - FIXED single version"""
        lines = code.strip().split('\n')
        line_count = len(lines)
        non_empty = [l for l in lines if l.strip()]

        analysis = f"📊 Code Analysis ({line_count} lines, {len(non_empty)} non-empty):\n\n"

        # Detect language
        lang = "Unknown"
        if '#include' in code:
            if 'iostream' in code or 'cout' in code or 'class ' in code:
                lang = "C++"
            else:
                lang = "C"
        elif 'def ' in code or 'import ' in code or 'print(' in code:
            lang = "Python"
        elif 'public static void main' in code:
            lang = "Java"
        elif '<?php' in code:
            lang = "PHP"
        elif 'function ' in code or 'const ' in code or 'let ' in code:
            lang = "JavaScript"
        elif '<html' in code.lower() or '<div' in code.lower():
            lang = "HTML"
        elif 'SELECT' in code.upper() or 'CREATE TABLE' in code.upper():
            lang = "SQL"

        analysis += f"📝 Language: {lang}\n\n"

        # Issues
        issues = []

        # Bracket matching
        if code.count('{') != code.count('}'):
            diff = code.count('{') - code.count('}')
            if diff > 0:
                issues.append(f"⚠ Missing {diff} closing brace(s) " + "}")
            else:
                issues.append(f"⚠ Extra {abs(diff)} closing brace(s) " + "}")

        if code.count('(') != code.count(')'):
            diff = code.count('(') - code.count(')')
            if diff > 0:
                issues.append(f"⚠ Missing {diff} closing parenthesis )")
            else:
                issues.append(f"⚠ Extra {abs(diff)} closing parenthesis )")

        if code.count('[') != code.count(']'):
            issues.append("⚠ Mismatched square brackets [ ]")

        # Quote matching (basic)
        double_quotes = code.count('"')
        if double_quotes % 2 != 0:
            # Exclude escaped quotes roughly
            unescaped = code.replace('\\"', '')
            if unescaped.count('"') % 2 != 0:
                issues.append("⚠ Possibly mismatched double quotes \"")

        # C/C++ specific
        if lang in ["C", "C++"]:
            if 'main' not in code:
                issues.append("⚠ No main() function found")
            if 'int main' in code and 'return' not in code:
                issues.append("💡 Consider adding 'return 0;' at end of main")
            if 'printf' in code and '#include <stdio.h>' not in code and '#include <cstdio>' not in code:
                issues.append("💡 Add: #include <stdio.h>")
            if 'scanf' in code and '#include <stdio.h>' not in code:
                issues.append("💡 Add: #include <stdio.h>")
            if 'cout' in code and '#include <iostream>' not in code:
                issues.append("💡 Add: #include <iostream>")
            if ('cout' in code or 'cin' in code) and 'using namespace std' not in code and 'std::' not in code:
                issues.append("💡 Add: using namespace std; or use std:: prefix")
            if 'string ' in code and '#include <string>' not in code and '#include <string.h>' not in code and '#include <cstring>' not in code:
                issues.append("💡 Add: #include <string> or #include <string.h>")
            if 'vector' in code and '#include <vector>' not in code:
                issues.append("💡 Add: #include <vector>")
            if 'map' in code and '#include <map>' not in code and '#include <unordered_map>' not in code:
                if 'map<' in code or 'map <' in code:
                    issues.append("💡 Add: #include <map>")
            if ('sort(' in code or 'find(' in code) and '#include <algorithm>' not in code:
                issues.append("💡 Add: #include <algorithm>")
            if ('sqrt' in code or 'pow(' in code) and '#include <cmath>' not in code and '#include <math.h>' not in code:
                issues.append("💡 Add: #include <cmath> or #include <math.h>")
            if 'malloc' in code and 'free' not in code:
                issues.append("⚠ malloc() found but no free() — possible memory leak!")
            if 'new ' in code and 'delete' not in code and 'unique_ptr' not in code and 'shared_ptr' not in code:
                issues.append("⚠ 'new' found but no 'delete' — possible memory leak! Consider smart pointers.")
            if 'gets(' in code:
                issues.append("⚠ gets() is UNSAFE! Use fgets() instead.")
            if 'scanf' in code and '%s' in code:
                issues.append("⚠ scanf %s is unsafe! Use fgets() or limit width: %49s")
            if 'goto' in code:
                issues.append("⚠ 'goto' found — consider using loops/functions instead")

            # Check for missing semicolons (improved)
            semicolon_issues = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped and
                    len(stripped) > 5 and
                    not stripped.startswith('//') and
                    not stripped.startswith('#') and
                    not stripped.startswith('/*') and
                    not stripped.startswith('*') and
                    not stripped.startswith('*/') and
                    not stripped.endswith('{') and
                    not stripped.endswith('}') and
                    not stripped.endswith(';') and
                    not stripped.endswith(':') and
                    not stripped.endswith('*/') and
                    not stripped.endswith(',') and
                    not stripped.endswith('\\') and
                    not stripped.endswith('(') and
                    not any(stripped.split('(')[0].strip().endswith(kw) for kw in ['if', 'else', 'for', 'while', 'switch', 'do', 'try', 'catch']) and
                    'else' != stripped and
                    '{' not in stripped and
                    '}' not in stripped):
                    if semicolon_issues < 3:  # Limit to 3 warnings
                        issues.append(f"⚠ Line {i+1}: Possibly missing semicolon → {stripped[:50]}")
                    semicolon_issues += 1

            if semicolon_issues > 3:
                issues.append(f"⚠ ... and {semicolon_issues - 3} more possible missing semicolons")

        # Python specific
        elif lang == "Python":
            for i, line in enumerate(lines):
                if '\t' in line and '    ' in code:
                    issues.append(f"⚠ Line {i+1}: Mixing tabs and spaces — use spaces only!")
                    break
            if 'except:' in code and 'except Exception' not in code:
                issues.append("💡 Use 'except Exception as e:' instead of bare 'except:'")
            if '== None' in code:
                issues.append("💡 Use 'is None' instead of '== None'")
            if '== True' in code:
                issues.append("💡 Use 'if variable:' instead of 'if variable == True:'")
            if 'print ' in code and 'print(' not in code:
                issues.append("⚠ Use print() with parentheses (Python 3)")
            if 'open(' in code and 'with ' not in code:
                issues.append("💡 Use 'with open()' for automatic file closing")
            if 'input(' in code and 'try' not in code:
                issues.append("💡 Consider wrapping input() in try-except for error handling")

        # Java specific
        elif lang == "Java":
            if 'public class' not in code:
                issues.append("💡 Java code should be inside a public class")
            if '==' in code and '"' in code:
                # Check if comparing strings with ==
                for line in lines:
                    if '==' in line and '"' in line and '.equals' not in line:
                        issues.append("💡 Use .equals() for string comparison in Java, not ==")
                        break
            if 'ArrayList' in code and 'import java.util' not in code:
                issues.append("💡 Add: import java.util.ArrayList;")
            if 'Scanner' in code and 'import java.util.Scanner' not in code:
                issues.append("💡 Add: import java.util.Scanner;")

        # JavaScript specific
        elif lang == "JavaScript":
            if 'var ' in code:
                issues.append("💡 Use 'let' or 'const' instead of 'var' (modern JS)")
            if '==' in code and '===' not in code:
                issues.append("💡 Use === (strict equality) instead of == (loose)")
            if 'document.write' in code:
                issues.append("⚠ Avoid document.write() — use DOM methods instead")

        # HTML specific
        elif lang == "HTML":
            if '<!DOCTYPE' not in code and '<!doctype' not in code:
                issues.append("💡 Add: <!DOCTYPE html> at the top")
            if '<meta charset' not in code:
                issues.append("💡 Add: <meta charset=\"UTF-8\"> in <head>")

        # PHP specific
        elif lang == "PHP":
            if '<?php' not in code:
                issues.append("💡 Add <?php at the beginning")
            if '$_GET' in code or '$_POST' in code:
                if 'htmlspecialchars' not in code and 'filter_input' not in code:
                    issues.append("⚠ Sanitize user input! Use htmlspecialchars() or filter_input()")

        # General checks
        for i, line in enumerate(lines):
            if len(line) > 120:
                issues.append(f"📏 Line {i+1}: Very long line ({len(line)} chars) — consider breaking")
                break  # Only warn once

        # Functions found
        funcs = []
        if lang in ["C", "C++"]:
            funcs = re.findall(r'\b([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{', code)
        elif lang == "Python":
            funcs = re.findall(r'def\s+(\w+)', code)
        elif lang == "Java":
            funcs = re.findall(r'(?:public|private|protected|static|\s)+[\w<>$$$$]+\s+(\w+)\s*\(', code)
        elif lang == "JavaScript":
            funcs = re.findall(r'function\s+(\w+)', code)
            funcs += re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>', code)
        elif lang == "PHP":
            funcs = re.findall(r'function\s+(\w+)', code)

        if funcs:
            unique_funcs = list(dict.fromkeys(funcs))[:15]
            analysis += f"🔧 Functions: {', '.join(unique_funcs)}\n\n"

        # Variables (basic detection)
        if lang in ["C", "C++"]:
            vars_found = re.findall(r'\b(?:int|float|double|char|string|bool|long|short|auto|unsigned)\s+(\w+)', code)
            if vars_found:
                unique_vars = list(dict.fromkeys(vars_found))[:10]
                analysis += f"📦 Variables: {', '.join(unique_vars)}\n\n"

        # Comments check
        comment_count = 0
        for l in lines:
            stripped = l.strip()
            if stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('/*') or stripped.startswith('*'):
                comment_count += 1

        if len(non_empty) > 10 and comment_count == 0:
            issues.append("💡 Add comments to explain your code logic")
        elif comment_count > 0:
            ratio = comment_count / max(len(non_empty), 1) * 100
            analysis += f"💬 Comment ratio: {ratio:.0f}% ({comment_count} comments)\n\n"

        # Report issues
        if issues:
            analysis += "🔍 Issues Found:\n"
            for issue in issues[:12]:
                analysis += f"  {issue}\n"
            if len(issues) > 12:
                analysis += f"  ... and {len(issues) - 12} more issues\n"
            analysis += "\n"
        else:
            analysis += "✅ No obvious issues detected! Code looks clean!\n\n"

        # Summary
        analysis += "📈 Summary:\n"
        if len(issues) == 0:
            analysis += "  Your code looks great! Good job! 👍\n"
        elif len(issues) <= 2:
            analysis += "  Minor issues found. Easy fixes! 👍\n"
        elif len(issues) <= 5:
            analysis += "  Several issues found. Review them one by one.\n"
        else:
            analysis += "  Multiple issues detected. Start with the first few and work down.\n"

        if self.context.get("mood") == "frustrated":
            analysis += "\n💪 Don't worry! Every programmer deals with bugs.\n"
            analysis += "Fix them one at a time and you'll get there! 🚀"

        # Context-specific tips
        if self.context.get("language"):
            analysis += f"\n\n💡 Detected language: {self.context['language']}"
            if self.context['language'] in ["C", "C++"]:
                analysis += "\n   Compile with: gcc -Wall -Wextra file.c -o program"
            elif self.context['language'] == "Python":
                analysis += "\n   Run with: python file.py"

        return analysis

    # =============================================
    # PUBLIC METHODS (SINGLE VERSION - FIXED)
    # =============================================
    def send_message(self, message, code, callback):
        """Process message and return response (fully offline) - FIXED"""
        def _process():
            try:
                response = self._find_response(message, code)

                # Only learn from GOOD responses (not generic fallbacks)
                if (response and
                    "I'm not sure" not in response and
                    "I understood:" not in response and
                    len(message.strip()) > 3):
                    self.knowledge.learn(message, response)

                # Store in conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": message
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                self.session_count += 1
                callback(response, None)
            except Exception as e:
                callback(f"Sorry, I had an issue processing that: {str(e)}\nPlease try again!", None)

        threading.Thread(target=_process, daemon=True).start()

    def get_suggestions(self, code, callback):
        """Generate smart code suggestions - FIXED single version"""
        def _process():
            try:
                suggestions = []
                if not code.strip():
                    callback("Write some code first to get suggestions.", None)
                    return

                lines = code.split('\n')
                non_empty = [l for l in lines if l.strip()]

                # Detect language
                lang = "Unknown"
                if '#include' in code:
                    if 'iostream' in code or 'cout' in code:
                        lang = "C++"
                    else:
                        lang = "C/C++"
                elif 'def ' in code or 'import ' in code or 'print(' in code:
                    lang = "Python"
                elif 'public static void main' in code:
                    lang = "Java"
                elif '<?php' in code:
                    lang = "PHP"
                elif 'function ' in code or 'let ' in code or 'const ' in code:
                    lang = "JavaScript"
                elif '<html' in code.lower():
                    lang = "HTML"
                elif 'SELECT' in code.upper() or 'CREATE TABLE' in code.upper():
                    lang = "SQL"

                suggestions.append(f"📝 Language: {lang}")
                suggestions.append(f"📏 Lines: {len(lines)} ({len(non_empty)} non-empty)")
                suggestions.append("")

                # C/C++ suggestions
                if lang in ["C/C++", "C++"]:
                    if '#include <iostream>' not in code and 'cout' in code:
                        suggestions.append("💡 Add: #include <iostream>")
                    if '#include <stdio.h>' not in code and 'printf' in code:
                        suggestions.append("💡 Add: #include <stdio.h>")
                    if '#include <string>' not in code and '#include <string.h>' not in code and 'string ' in code:
                        suggestions.append("💡 Add: #include <string> or #include <string.h>")
                    if '#include <vector>' not in code and 'vector' in code:
                        suggestions.append("💡 Add: #include <vector>")
                    if '#include <algorithm>' not in code and ('sort(' in code or 'find(' in code):
                        suggestions.append("💡 Add: #include <algorithm>")
                    if '#include <cmath>' not in code and '#include <math.h>' not in code:
                        if 'sqrt' in code or 'pow(' in code or 'abs(' in code:
                            suggestions.append("💡 Add: #include <cmath>")
                    if 'using namespace std' not in code and ('cout' in code or 'cin' in code or 'string ' in code):
                        if 'std::' not in code:
                            suggestions.append("💡 Add: using namespace std; (or use std:: prefix)")
                    if 'return 0' not in code and 'int main' in code:
                        suggestions.append("💡 Add 'return 0;' at end of main()")
                    if 'malloc' in code and 'free' not in code:
                        suggestions.append("⚠ malloc() without free() — memory leak risk!")
                    if 'new ' in code and 'delete' not in code:
                        if 'unique_ptr' not in code and 'shared_ptr' not in code:
                            suggestions.append("⚠ 'new' without 'delete' — consider smart pointers!")
                    if 'goto' in code:
                        suggestions.append("⚠ 'goto' found — consider using loops/functions instead")
                    if 'gets(' in code:
                        suggestions.append("⚠ gets() is unsafe! Use fgets() instead")
                    if 'scanf' in code and '%s' in code:
                        suggestions.append("⚠ scanf %s is unsafe! Use fgets() or limit width: %49s")

                # Python suggestions
                elif lang == "Python":
                    if 'except:' in code and 'except Exception' not in code:
                        suggestions.append("💡 Use 'except Exception as e:' instead of bare 'except:'")
                    if 'input(' in code and 'try' not in code:
                        suggestions.append("💡 Wrap input() in try-except for error handling")
                    if '== None' in code:
                        suggestions.append("💡 Use 'is None' instead of '== None'")
                    if '== True' in code:
                        suggestions.append("💡 Use 'if variable:' instead of 'if variable == True:'")
                    if 'print ' in code and 'print(' not in code:
                        suggestions.append("⚠ Use print() with parentheses (Python 3)")
                    has_main = 'if __name__' in code
                    has_def = 'def ' in code
                    if has_def and not has_main:
                        suggestions.append("💡 Add: if __name__ == '__main__': main()")
                    if 'open(' in code and 'with ' not in code:
                        suggestions.append("💡 Use 'with open()' for automatic file closing")

                # Java suggestions
                elif lang == "Java":
                    if 'System.out.println' in code and 'public class' not in code:
                        suggestions.append("💡 Code should be inside a public class")
                    if '== ' in code and '"' in code:
                        suggestions.append("💡 Use .equals() for string comparison, not ==")
                    if 'ArrayList' in code and 'import java.util' not in code:
                        suggestions.append("💡 Add: import java.util.ArrayList;")
                    if 'Scanner' in code and 'import java.util.Scanner' not in code:
                        suggestions.append("💡 Add: import java.util.Scanner;")

                # JavaScript suggestions
                elif lang == "JavaScript":
                    if 'var ' in code:
                        suggestions.append("💡 Use 'let' or 'const' instead of 'var' (modern JS)")
                    if '==' in code and '===' not in code:
                        suggestions.append("💡 Use === (strict equality) instead of == (loose)")
                    if 'document.write' in code:
                        suggestions.append("⚠ Avoid document.write() — use DOM methods instead")

                # HTML suggestions
                elif lang == "HTML":
                    if '<!DOCTYPE' not in code and '<!doctype' not in code:
                        suggestions.append("💡 Add: <!DOCTYPE html> at the top")
                    if '<meta charset' not in code:
                        suggestions.append("💡 Add: <meta charset=\"UTF-8\"> in <head>")
                    if '<meta name=\"viewport\"' not in code:
                        suggestions.append("💡 Add viewport meta tag for mobile responsiveness")

                # PHP suggestions
                elif lang == "PHP":
                    if '<?php' not in code:
                        suggestions.append("💡 Add <?php at the beginning")
                    if '$_GET' in code or '$_POST' in code:
                        if 'htmlspecialchars' not in code:
                            suggestions.append("⚠ Sanitize user input with htmlspecialchars()")

                # General checks
                suggestions.append("")

                if code.count('{') != code.count('}'):
                    suggestions.append("⚠ Mismatched curly braces { }")
                if code.count('(') != code.count(')'):
                    suggestions.append("⚠ Mismatched parentheses ( )")
                if code.count('[') != code.count(']'):
                    suggestions.append("⚠ Mismatched square brackets [ ]")

                # Long lines
                long_lines = [(i+1, len(l)) for i, l in enumerate(lines) if len(l) > 100]
                for ln, length in long_lines[:3]:
                    suggestions.append(f"📏 Line {ln}: Consider breaking ({length} chars)")

                # Comments check
                comment_count = sum(1 for l in lines if l.strip().startswith('//') or l.strip().startswith('#'))
                if len(non_empty) > 10 and comment_count == 0:
                    suggestions.append("💡 Add comments to explain your code")
                elif comment_count > 0:
                    ratio = comment_count / max(len(non_empty), 1) * 100
                    suggestions.append(f"💬 Comment ratio: {ratio:.0f}% ({comment_count} comments)")

                # Function count
                if lang in ["C/C++", "C++"]:
                    func_count = len(re.findall(r'\b\w+\s*\([^)]*\)\s*\{', code))
                elif lang == "Python":
                    func_count = len(re.findall(r'def\s+\w+', code))
                elif lang == "Java":
                    func_count = len(re.findall(r'(?:public|private|protected|static|\s)+[\w<>$$$$]+\s+\w+\s*\(', code))
                else:
                    func_count = len(re.findall(r'function\s+\w+', code))

                if func_count > 0:
                    suggestions.append(f"🔧 Functions found: {func_count}")

                if not suggestions or all(s == "" or s is None for s in suggestions):
                    suggestions.append("✅ Code looks good! No suggestions.")

                # Clean up
                result = "\n".join(s for s in suggestions if s is not None)
                callback(result, None)

            except Exception as e:
                callback(None, str(e))

        threading.Thread(target=_process, daemon=True).start()
            

class CompilerService:
    """Handles code compilation and execution"""

    def __init__(self):
        self.compiler = "clang++"
        self.output_path = None

    def set_compiler(self, compiler):
        self.compiler = compiler

    def compile(self, source_file, callback=None):
        def _compile():
            try:
                base = os.path.splitext(source_file)[0]
                self.output_path = base + ('.exe' if os.name == 'nt' else '')

                if self.compiler == 'cl':
                    cmd = ['cl', '/EHsc', '/W4', f'/Fe:{self.output_path}', source_file]
                else:
                    cmd = [self.compiler, '-std=c++17', '-Wall', '-o', self.output_path, source_file]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
                success = result.returncode == 0

                if callback:
                    callback(success, output if output else "Compilation successful!")
            except FileNotFoundError:
                if callback:
                    callback(False, f"Compiler '{self.compiler}' not found. Please install it or check PATH.")
            except subprocess.TimeoutExpired:
                if callback:
                    callback(False, "Compilation timed out.")
            except Exception as e:
                if callback:
                    callback(False, str(e))

        thread = threading.Thread(target=_compile, daemon=True)
        thread.start()

    def run(self, callback=None):
        def _run():
            try:
                if not self.output_path or not os.path.exists(self.output_path):
                    if callback:
                        callback("No executable found. Please compile first.")
                    return

                result = subprocess.run([self.output_path], capture_output=True, text=True, timeout=30)
                output = result.stdout
                if result.stderr:
                    output += "\n[stderr]:\n" + result.stderr
                output += f"\n\n[Exit code: {result.returncode}]"

                if callback:
                    callback(output)
            except subprocess.TimeoutExpired:
                if callback:
                    callback("Program execution timed out (30s limit).")
            except Exception as e:
                if callback:
                    callback(f"Error: {str(e)}")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()


# ============================================================
# Chat Session Manager
# ============================================================
class ChatSessionManager:
    """Manages chat sessions - save, load, list"""

    def __init__(self):
        self.chats_dir = FOLDERS["chats"]
        self.current_session_id = None
        self.current_messages = []

    def new_session(self):
        """Start a new chat session"""
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.current_messages = []
        return self.current_session_id

    def add_message(self, sender, message):
        """Add message to current session"""
        self.current_messages.append({
            "sender": sender,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        self._save_current()

    def _save_current(self):
        """Save current session to JSON file"""
        if not self.current_session_id or not self.current_messages:
            return

        title = self.current_messages[0]["message"][:50] if self.current_messages else "Untitled"

        data = {
            "id": self.current_session_id,
            "title": title,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": self.current_messages
        }

        filepath = os.path.join(self.chats_dir, f"{self.current_session_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_session(self, session_id):
        """Load a chat session by ID"""
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.current_session_id = data["id"]
                self.current_messages = data.get("messages", [])
                return data
        except Exception:
            return None

    def list_sessions(self):
        """List all saved chat sessions"""
        sessions = []
        try:
            for filename in sorted(os.listdir(self.chats_dir), reverse=True):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.chats_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            sessions.append({
                                "id": data.get("id", filename.replace(".json", "")),
                                "title": data.get("title", "Untitled"),
                                "created": data.get("created", "Unknown")
                            })
                    except Exception:
                        continue
        except Exception:
            pass
        return sessions

    def delete_session(self, session_id):
        """Delete a chat session"""
        filepath = os.path.join(self.chats_dir, f"{session_id}.json")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception:
            pass
        return False


# ============================================================
# Main Application
# ============================================================
class AICodeEditor:
    """Main application window"""

    def _on_text_modified(self, event=None):
        self.editor.edit_modified(False)
        self.is_modified = True
        self._update_title()

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Code Editor")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)

        # Dark theme colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'accent': '#0078d7',
            'editor_bg': '#1e1e1e',
            'panel_bg': '#252526',
            'border': '#3d3d3d',
            'button': '#0e639c',
            'button_hover': '#1177bb',
            'success': '#4ec9b0',
            'error': '#f14c4c',
            'history_bg': '#1e1e2e',
            'history_item': '#2d2d3d',
        }

        self.root.configure(bg=self.colors['bg'])

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Dark.TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('Dark.TButton', background=self.colors['button'], foreground='white')
        style.configure('Dark.TNotebook', background=self.colors['panel_bg'])
        style.configure('Dark.TNotebook.Tab', background=self.colors['panel_bg'],
                        foreground=self.colors['fg'], padding=[10, 5])
        style.map('Dark.TNotebook.Tab', background=[('selected', self.colors['bg'])])

        # Services
        self.ai_service = AIService()
        self.compiler_service = CompilerService()
        self.chat_manager = ChatSessionManager()

        # State
        self.current_file = None
        self.is_modified = False

        self._setup_ui()
        self._setup_menu()
        self._setup_bindings()
        self._load_chat_history()

    def _setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar = tk.Frame(main_frame, bg=self.colors['panel_bg'], height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        btn_style = {'bg': self.colors['button'], 'fg': 'white', 'relief': 'flat', 'padx': 10, 'pady': 5}

        tk.Button(toolbar, text="New", command=self.new_file, **btn_style).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(toolbar, text="Open", command=self.open_file, **btn_style).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(toolbar, text="Save", command=self.save_file, **btn_style).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(toolbar, text="Open Project", command=self.open_project_folder, **btn_style).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(toolbar, text="Open Headers",
                  command=lambda: self._open_specific_folder("headers"),
                  **btn_style).pack(side=tk.LEFT, padx=2, pady=5)

        self.compile_btn = tk.Button(toolbar, text="▶ Compile", command=self.compile_code, **btn_style)
        self.compile_btn.pack(side=tk.LEFT, padx=2, pady=5)

        tk.Button(toolbar, text="▶ Run", command=self.run_code, **btn_style).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Button(toolbar, text="▶ Build & Run", command=self.build_and_run,
                  bg='#107c10', fg='white', relief='flat', padx=10, pady=5).pack(side=tk.LEFT, padx=2, pady=5)

        # ============ THREE PANEL LAYOUT ============
        paned_main = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg=self.colors['border'], sashwidth=4)
        paned_main.pack(fill=tk.BOTH, expand=True)

        # ================= LEFT: HISTORY PANEL =================
        history_frame = tk.Frame(paned_main, bg=self.colors['history_bg'], width=200)

        tk.Label(
            history_frame,
            text="📂 Chat History",
            bg=self.colors['history_bg'],
            fg=self.colors['accent'],
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor=tk.W, padx=8, pady=(8, 4))

        # New Chat button
        tk.Button(
            history_frame,
            text="+ New Chat",
            command=self.new_chat_session,
            bg='#107c10',
            fg='white',
            relief='flat',
            font=('Segoe UI', 10),
            padx=10, pady=4
        ).pack(fill=tk.X, padx=8, pady=4)

        # History listbox
        self.history_listbox = tk.Listbox(
            history_frame,
            bg=self.colors['history_bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 10),
            selectbackground=self.colors['accent'],
            selectforeground='white',
            borderwidth=0,
            highlightthickness=0,
            activestyle='none'
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_select)

        # Delete chat button
        tk.Button(
            history_frame,
            text="🗑 Delete Chat",
            command=self.delete_selected_chat,
            bg='#a02020',
            fg='white',
            relief='flat',
            font=('Segoe UI', 9),
            padx=8, pady=3
        ).pack(fill=tk.X, padx=8, pady=(0, 8))

        paned_main.add(history_frame, minsize=180)

        # Store session IDs for listbox mapping
        self.history_session_ids = []

        # ================= MIDDLE: EDITOR =================
        editor_frame = tk.Frame(paned_main, bg=self.colors['bg'])
        editor_container = tk.Frame(editor_frame, bg=self.colors['bg'])
        editor_container.pack(fill=tk.BOTH, expand=True)

        self.line_numbers = tk.Text(editor_container, width=4, bg="#1e1e1e",
                                    fg="red", state='disabled', font=EDITOR_FONT)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(editor_container, bg=self.colors['editor_bg'],
                              fg=self.colors['fg'], wrap=tk.NONE,
                              undo=True, tabs='4c', font=EDITOR_FONT)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.editor.bind("<<Modified>>", self._on_text_modified)

        editor_scroll_y = ttk.Scrollbar(editor_container, command=self._scroll_both)
        editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=editor_scroll_y.set)

        editor_scroll_x = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.editor.xview)
        editor_scroll_x.pack(fill=tk.X)
        self.editor.config(xscrollcommand=editor_scroll_x.set)

        self.highlighter = SyntaxHighlighter(self.editor)
        paned_main.add(editor_frame, minsize=400)

        # ================= RIGHT: AI PANEL =================
        ai_frame = tk.Frame(paned_main, bg=self.colors['panel_bg'])
        paned_main.add(ai_frame, minsize=300)

        self.notebook = ttk.Notebook(ai_frame, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ========= Chat tab =========
        chat_frame = tk.Frame(self.notebook, bg=self.colors['panel_bg'])
        self.notebook.add(chat_frame, text="💬 Chat")

        tk.Label(
            chat_frame,
            text="💬 AI Assistant (Offline)",
            bg=self.colors['panel_bg'],
            fg=self.colors['accent'],
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor=tk.W, padx=10, pady=5)

        self.chat_history = scrolledtext.ScrolledText(
            chat_frame,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 11),
            wrap=tk.WORD,
            state='disabled'
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Chat input area
        chat_input_container = tk.Frame(chat_frame, bg=self.colors['panel_bg'])
        chat_input_container.pack(fill=tk.X, padx=10, pady=8)

        self.chat_input = scrolledtext.ScrolledText(
            chat_input_container,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            insertbackground='white',
            font=('Segoe UI', 11),
            height=5,
            wrap=tk.WORD
        )
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.chat_input.configure(width=30)
        self.chat_input.bind('<Control-Return>', lambda e: self.send_chat())

        send_btn = tk.Button(
            chat_input_container,
            text="Send\n(Ctrl+Enter)",
            command=self.send_chat,
            bg=self.colors['button'],
            fg='white',
            relief='flat',
            width=12,
            height=3
        )
        send_btn.pack(side=tk.RIGHT)

        # ========= Ideas tab =========
        suggestions_frame = tk.Frame(self.notebook, bg=self.colors['panel_bg'])
        self.notebook.add(suggestions_frame, text="💡 Ideas")

        tk.Label(suggestions_frame, text="💡 Ideas & Suggestions",
                 bg=self.colors['panel_bg'], fg=self.colors['accent'],
                 font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=5)

        self.suggestions_list = tk.Listbox(
            suggestions_frame, bg=self.colors['bg'], fg=self.colors['fg'],
            font=('Segoe UI', 10), selectbackground=self.colors['accent']
        )
        self.suggestions_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Button(suggestions_frame, text="🔍 Get Suggestions",
                  command=self.get_suggestions, bg=self.colors['button'],
                  fg='white', relief='flat', padx=15, pady=5).pack(pady=10)

        # ========= Output tab =========
        output_frame = tk.Frame(self.notebook, bg=self.colors['panel_bg'])
        self.notebook.add(output_frame, text="📋 Output")

        tk.Label(output_frame, text="📋 Compiler Output",
                 bg=self.colors['panel_bg'], fg=self.colors['accent'],
                 font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(
            output_frame, bg='#1a1a1a', fg=self.colors['fg'],
            font=('Consolas', 10), wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Button(output_frame, text="Clear",
                  command=lambda: self.output_text.delete('1.0', tk.END),
                  bg='#4d4d4d', fg='white', relief='flat').pack(pady=5)

        # Status bar
        self.status_bar = tk.Label(
            self.root, text="Ready | Offline Mode",
            bg=self.colors['accent'],
            fg='white', anchor=tk.W, padx=10
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _scroll_both(self, *args):
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    # ============================================================
    # Chat History Panel Methods
    # ============================================================
    def _load_chat_history(self):
        """Load all saved chats into history panel"""
        self.history_listbox.delete(0, tk.END)
        self.history_session_ids = []

        sessions = self.chat_manager.list_sessions()
        for session in sessions:
            title = session["title"][:40]
            display = f"💬 {title}"
            self.history_listbox.insert(tk.END, display)
            self.history_session_ids.append(session["id"])

    def _on_history_select(self, event=None):
        """Load selected chat from history"""
        selection = self.history_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.history_session_ids):
            session_id = self.history_session_ids[index]
            data = self.chat_manager.load_session(session_id)

            if data:
                # Clear chat display
                self.chat_history.config(state='normal')
                self.chat_history.delete('1.0', tk.END)
                self.chat_history.config(state='disabled')

                # Display all messages
                for msg in data.get("messages", []):
                    sender = msg.get("sender", "Unknown")
                    content = msg.get("message", "")
                    is_user = sender == "You"
                    self._append_chat(sender, content, is_user=is_user)

                self.status_bar.config(text=f"Loaded chat: {data.get('title', 'Untitled')[:40]}")

    def new_chat_session(self):
        """Start a brand new chat session"""
        self.chat_manager.new_session()

        # Clear chat display
        self.chat_history.config(state='normal')
        self.chat_history.delete('1.0', tk.END)
        self.chat_history.config(state='disabled')

        self._append_chat("AI", "New chat started! How can I help you?", is_user=False)
        self.status_bar.config(text="New chat session started")

    def delete_selected_chat(self):
        """Delete selected chat from history"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Select a chat to delete.")
            return

        index = selection[0]
        if index < len(self.history_session_ids):
            if messagebox.askyesno("Delete Chat", "Are you sure you want to delete this chat?"):
                session_id = self.history_session_ids[index]
                self.chat_manager.delete_session(session_id)
                self._load_chat_history()
                self.status_bar.config(text="Chat deleted")

    # ============================================================
    # Menu, Bindings, Context Menus (UNCHANGED)
    # ============================================================
    def _setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_command(label="Open Project", command=self.open_project_folder)
        file_menu.add_command(label="Open Headers",
                              command=lambda: self._open_specific_folder("headers"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        build_menu = tk.Menu(menubar, tearoff=0)
        build_menu.add_command(label="Compile", command=self.compile_code, accelerator="Ctrl+B")
        build_menu.add_command(label="Run", command=self.run_code, accelerator="Ctrl+R")
        build_menu.add_command(label="Build & Run", command=self.build_and_run, accelerator="F5")
        menubar.add_cascade(label="Build", menu=build_menu)

        # Chat menu
        chat_menu = tk.Menu(menubar, tearoff=0)
        chat_menu.add_command(label="New Chat", command=self.new_chat_session)
        chat_menu.add_command(label="Delete Selected Chat", command=self.delete_selected_chat)
        menubar.add_cascade(label="Chat", menu=chat_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _setup_bindings(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-b>', lambda e: self.compile_code())
        self.root.bind('<Control-r>', lambda e: self.run_code())
        self.root.bind('<F5>', lambda e: self.build_and_run())

        self.editor.bind('<KeyRelease>', self._on_editor_change)
        self.editor.bind('<MouseWheel>', lambda e: self._update_line_numbers())

        self._setup_context_menus()

    def _setup_context_menus(self):
        self.editor_menu = tk.Menu(self.root, tearoff=0)
        self.editor_menu.add_command(label="Cut", command=lambda: self.editor.event_generate("<<Cut>>"))
        self.editor_menu.add_command(label="Copy", command=lambda: self.editor.event_generate("<<Copy>>"))
        self.editor_menu.add_command(label="Paste", command=lambda: self.editor.event_generate("<<Paste>>"))
        self.editor_menu.add_separator()
        self.editor_menu.add_command(label="Select All",
                                     command=lambda: self.editor.tag_add("sel", "1.0", "end"))
        self.editor.bind("<Button-3>", lambda e: self._show_context_menu(e, self.editor_menu))

        self.chat_menu_ctx = tk.Menu(self.root, tearoff=0)
        self.chat_menu_ctx.add_command(label="Copy",
                                       command=lambda: self._copy_from_widget(self.chat_history))
        self.chat_menu_ctx.add_command(label="Paste", command=lambda: self._paste_to_chat_input())
        self.chat_menu_ctx.add_command(label="Select All",
                                       command=lambda: self._select_all_readonly(self.chat_history))
        self.chat_history.bind("<Button-3>", lambda e: self._show_context_menu(e, self.chat_menu_ctx))

        self.output_menu = tk.Menu(self.root, tearoff=0)
        self.output_menu.add_command(label="Copy",
                                     command=lambda: self._copy_from_widget(self.output_text))
        self.output_menu.add_command(label="Select All",
                                     command=lambda: self._select_all_readonly(self.output_text))
        self.output_text.bind("<Button-3>", lambda e: self._show_context_menu(e, self.output_menu))

        self.chat_input_menu = tk.Menu(self.root, tearoff=0)
        self.chat_input_menu.add_command(label="Cut",
                                         command=lambda: self.chat_input.event_generate("<<Cut>>"))
        self.chat_input_menu.add_command(label="Copy",
                                         command=lambda: self.chat_input.event_generate("<<Copy>>"))
        self.chat_input_menu.add_command(label="Paste",
                                         command=lambda: self.chat_input.event_generate("<<Paste>>"))
        self.chat_input_menu.add_separator()
        self.chat_input_menu.add_command(label="Select All",
                                         command=lambda: self.chat_input.tag_add(tk.SEL, '1.0', tk.END))
        self.chat_input.bind("<Button-3>", lambda e: self._show_context_menu(e, self.chat_input_menu))

        self.chat_history.bind("<Control-c>", lambda e: self._copy_from_widget(self.chat_history))
        self.output_text.bind("<Control-c>", lambda e: self._copy_from_widget(self.output_text))

    def _update_compile_visibility(self):
        if not self.current_file:
            self.compile_btn.pack_forget()
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext in [".c", ".cpp"]:
            self.compile_btn.pack(side=tk.LEFT, padx=2, pady=5)
        else:
            self.compile_btn.pack_forget()

    def _show_context_menu(self, event, menu):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_from_widget(self, widget):
        try:
            widget.config(state='normal')
            if widget.tag_ranges("sel"):
                selected_text = widget.get("sel.first", "sel.last")
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
            widget.config(state='disabled')
        except tk.TclError:
            pass

    def _select_all_readonly(self, widget):
        widget.config(state='normal')
        widget.tag_add("sel", "1.0", "end")
        widget.config(state='disabled')

    def _paste_to_chat_input(self):
        try:
            text = self.root.clipboard_get()
            self.chat_input.insert(tk.INSERT, text)
            self.chat_input.focus_set()
        except tk.TclError:
            pass

    def _on_editor_change(self, event=None):
        self.is_modified = True
        self._update_title()
        self._update_line_numbers()
        self.highlighter.highlight()

    def _update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        line_count = int(self.editor.index('end-1c').split('.')[0])
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')

    def _update_title(self):
        title = "AI Code Editor"
        if self.current_file:
            title = os.path.basename(self.current_file) + " - " + title
        if self.is_modified:
            title = "• " + title
        self.root.title(title)

    # ============================================================
    # File Operations (UNCHANGED)
    # ============================================================
    def new_file(self):
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "Discard unsaved changes?"):
                return
        self.editor.delete('1.0', tk.END)
        self.current_file = None
        self.is_modified = False
        self._update_title()
        self._update_line_numbers()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Files", "*.c *.cpp *.h *.hpp *.py *.java *.php *.html *.css *.js *.sql"),
                ("C / C++ files", "*.c *.cpp *.h *.hpp"),
                ("Python files", "*.py"),
                ("Java files", "*.java"),
                ("PHP files", "*.php"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JavaScript files", "*.js"),
                ("SQL files", "*.sql"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', f.read())
            self.current_file = file_path
            self.is_modified = False
            self._update_title()
            self._update_line_numbers()
            self.highlighter.highlight()
            self.status_bar.config(text=f"Opened: {file_path}")
            self._update_compile_visibility()

    def save_file(self):
        if not self.current_file:
            self.save_file_as()
            return
        try:
            content = self.editor.get("1.0", tk.END)
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.is_modified = False
            self._update_title()
            self.status_bar.config(text=f"Saved: {self.current_file}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
        self._update_compile_visibility()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("All supported files", "*.c *.cpp *.h *.hpp *.py *.java *.php *.html *.css *.js *.sql"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return
        try:
            content = self.editor.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.current_file = file_path
            self.is_modified = False
            self._update_title()
            self.status_bar.config(text=f"Saved: {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
        self._update_compile_visibility()

    def open_project_folder(self):
        folder_path = filedialog.askdirectory(title="Select Project Folder")
        if not folder_path:
            return

        allowed_extensions = (
            ".c", ".cpp", ".h", ".hpp",
            ".py", ".java", ".php",
            ".html", ".css", ".js", ".sql"
        )

        found_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    full_path = os.path.join(root, file)
                    found_files.append(full_path)

        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"Project Folder: {folder_path}\n\n")

        if not found_files:
            self.output_text.insert("end", "No supported files found.\n")
        else:
            for f in found_files:
                self.output_text.insert("end", f + "\n")

        self.status_bar.config(text=f"Loaded {len(found_files)} project files")

    def _open_specific_folder(self, folder_name):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(base_dir, folder_name)

        if not os.path.exists(target_path):
            messagebox.showerror("Folder Not Found", f"{folder_name} folder not found.")
            return

        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"{folder_name} Folder:\n\n")

        for root, dirs, files in os.walk(target_path):
            for file in files:
                self.output_text.insert("end", os.path.join(root, file) + "\n")

        self.status_bar.config(text=f"{folder_name} loaded")

    # ============================================================
    # Compile & Run (UNCHANGED)
    # ============================================================
    def compile_code(self):
        if not self.current_file:
            self.save_file_as()
            if not self.current_file:
                return
        elif self.is_modified:
            self.save_file()

        self.status_bar.config(text="Compiling...")
        self.notebook.select(2)

        def on_compile(success, output):
            self.output_text.delete('1.0', tk.END)
            if success:
                self.output_text.insert(tk.END, "✓ Compilation successful!\n\n" + output)
                self.status_bar.config(text="Compilation successful")
            else:
                self.output_text.insert(tk.END, "✗ Compilation failed:\n\n" + output)
                self.status_bar.config(text="Compilation failed")

        self.compiler_service.compile(
            self.current_file,
            callback=lambda s, o: self.root.after(0, lambda: on_compile(s, o))
        )

    def run_code(self):
        if not self.current_file:
            messagebox.showwarning("No File", "Please save the file first.")
            return

        file_path = self.current_file
        ext = os.path.splitext(file_path)[1].lower()

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"▶ Running: {file_path}\n\n")

        try:
            if ext == ".py":
                cmd = ["python", file_path]
            elif ext == ".js":
                cmd = ["node", file_path]
            elif ext == ".php":
                cmd = ["php", file_path]
            elif ext == ".html":
                webbrowser.open(file_path)
                self.output_text.insert(tk.END, "Opened in browser.\n")
                return
            elif ext in [".c", ".cpp"]:
                self.compile_code()
                return
            else:
                self.output_text.insert(tk.END, f"Cannot run this file type: {ext}\n")
                return

            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.stdout:
                self.output_text.insert(tk.END, result.stdout)
            if result.stderr:
                self.output_text.insert(tk.END, result.stderr)
            self.status_bar.config(text="Run completed")

        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")
            self.status_bar.config
            
    def build_and_run(self):
        if not self.current_file:
            messagebox.showwarning("No File", "Please save the file first.")
            return

        ext = os.path.splitext(self.current_file)[1].lower()

        if ext in [".c", ".cpp"]:
            self.compile_code()
        else:
            self.run_code()

    # ============================================================
    # Chat System (MODIFIED - Offline)
    # ============================================================
    def send_chat(self):
        message = self.chat_input.get('1.0', tk.END).strip()
        if not message:
            return

        self.chat_input.delete('1.0', tk.END)
        code = self.editor.get('1.0', tk.END)

        # Start new session if needed
        if not self.chat_manager.current_session_id:
            self.chat_manager.new_session()

        # Add user message
        self._append_chat("You", message, is_user=True)
        self.chat_manager.add_message("You", message)
        self.status_bar.config(text="AI is thinking...")

        def on_response(response, error):
            if error:
                self._append_chat("Error", error, is_error=True)
            else:
                self._append_chat("AI", response, is_user=False)
                self.chat_manager.add_message("AI", response)
            self.status_bar.config(text="Ready | Offline Mode")
            # Refresh history panel
            self._load_chat_history()

        self.ai_service.send_message(
            message,
            code,
            callback=lambda r, e: self.root.after(0, lambda: on_response(r, e))
        )

    def _append_chat(self, sender, message, is_user=False, is_error=False):
        self.chat_history.config(state='normal')

        if is_error:
            color = self.colors['error']
        elif is_user:
            color = self.colors['accent']
        else:
            color = self.colors['success']

        tag_name = f'sender_{sender}_{id(message)}'
        self.chat_history.insert(tk.END, f"\n[{sender}]\n", tag_name)
        self.chat_history.insert(tk.END, f"{message}\n")
        self.chat_history.tag_config(tag_name, foreground=color, font=('Segoe UI', 10, 'bold'))

        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

    def get_suggestions(self):
        code = self.editor.get('1.0', tk.END).strip()
        if not code:
            messagebox.showinfo("Info", "Write some code first to get suggestions.")
            return

        self.suggestions_list.delete(0, tk.END)
        self.suggestions_list.insert(tk.END, "🔄 Analyzing code...")
        self.status_bar.config(text="Getting suggestions...")

        def on_response(response, error):
            self.suggestions_list.delete(0, tk.END)
            if error:
                self.suggestions_list.insert(tk.END, f" {error}")
            else:
                lines = response.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self.suggestions_list.insert(tk.END, line.strip())
            self.status_bar.config(text="Ready | Offline Mode")

        self.ai_service.get_suggestions(
            code,
            callback=lambda r, e: self.root.after(0, lambda: on_response(r, e))
        )

    def show_about(self):
        messagebox.showinfo("About AI Code Editor",
            "AI Code Editor v2.0 (Offline)\n\n"
            "A fully offline AI-style code editor.\n\n"
            "Features:\n"
            "• Syntax highlighting\n"
            "• Smart offline chat assistant\n"
            "• Chat history & memory\n"
            "• Knowledge base (learns from chats)\n"
            "• Code suggestions\n"
            "• Compiler integration\n\n"
            "No internet required.\n"
            "No external AI APIs.\n"
            "Runs on low-end systems.")

    def run(self):
        """Start the application"""
        self._update_line_numbers()
        self.root.mainloop()


# ============================================================
# START THE APP
# ============================================================
if __name__ == "__main__":
    app = AICodeEditor()
    app.run()