# OrChat

[![PyPI version](https://badge.fury.io/py/orchat.svg)](https://badge.fury.io/py/orchat)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)

A powerful CLI for chatting with AI models through OpenRouter with streaming responses, token tracking, and extensive customization options.

![OrChat screenshot](https://github.com/user-attachments/assets/b74094e2-dbeb-4707-a5dd-8b5f312bf997)

## ✨ Features

- **Universal Model Access**: Connect to any AI model available on OpenRouter
- **Interactive Chat**: Enjoy a smooth conversation experience with real-time streaming responses
- **Rich Markdown Rendering**: View formatted text, code blocks, tables and more directly in your terminal
- **Performance Analytics**: Track token usage and response times for cost efficiency
- **Multimodal Support**: Share images and various file types with compatible AI models
- **Smart Thinking Mode**: See the AI's reasoning process with compatible models
- **Extensible Plugin System**: Easily extend functionality with custom plugins
- **Multiple Export Formats**: Save conversations as Markdown, HTML, JSON, TXT, or PDF
- **Smart Context Management**: Automatically manages conversation history to stay within token limits
- **Customizable Themes**: Choose from different visual themes for your terminal
- **File Attachment Support**: Share files of various types with the AI for analysis

## 🚀 Installation

### From PyPI (Recommended)

```bash
pip install orchat
```

### From Source

```bash
git clone https://github.com/oop7/OrChat.git
pip install -r requirements.txt
python main.py
```

## 📋 Prerequisites

- Python 3.7 or higher
- An OpenRouter API key (get one at [OpenRouter.ai](https://openrouter.ai))
- Required packages: requests, tiktoken, rich, dotenv, colorama

## 🏁 Getting Started

1. Install OrChat using one of the methods above
2. Run the setup wizard
   - if you follow from source PyPI:
     ```bash
     orchat --setup
     ```
   - if you follow from source method:
     ```bash
     python main.py --setup
     ```
3. Enter your OpenRouter API key when prompted
4. Select your preferred AI model and configure settings
5. Start chatting!

## 🪛 Add-Ons

### FZF fuzzy search

1. Install fzf and pyfzf

   - Install pyfzf
     ```bash
     pip install pyfzf
     ```
   - Fzf can be downloaded from https://github.com/junegunn/fzf?tab=readme-ov-file#installation

2. Ensure fzf is in your path
3. From now on, the model selection will use fzf to search!

## ⚙️ Configuration

OrChat can be configured in multiple ways:

1. **Setup Wizard**: Run `python main.py --setup` for interactive configuration
2. **Config File**: Edit the `config.ini` file in the application directory
3. **Environment Variables**: Create a `.env` file with your configuration
4. **System Environment Variables**: Set the OPENROUTER_API_KEY on the user/system environment.

Example `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
```

Example `config.ini` structure:

```ini
[API]
OPENROUTER_API_KEY = your_api_key_here

[SETTINGS]
MODEL = anthropic/claude-3-opus
TEMPERATURE = 0.7
SYSTEM_INSTRUCTIONS = You are a helpful AI assistant.
THEME = default
MAX_TOKENS = 8000
AUTOSAVE_INTERVAL = 300
STREAMING = True
THINKING_MODE = True
```

## 🖥️ Command-Line Options

- `--setup`: Run the setup wizard
- `--model MODEL`: Specify the model to use (e.g., `--model "anthropic/claude-3-opus"`)
- `--task {creative,coding,analysis,chat}`: Optimize for a specific task type
- `--image PATH`: Analyze an image file

## 💬 Chat Commands

| Command                   | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `/help`                   | Show available commands                               |
| `/exit`                   | Exit the chat                                         |
| `/quit`                   | Exit the chat                                         |
| `/new`                    | Start a new conversation                              |
| `/clear`                  | Clear conversation history                            |
| `/cls` or `/clear-screen` | Clear the terminal screen                             |
| `/save [format]`          | Save conversation (formats: md, html, json, txt, pdf) |
| `/model`                  | Change the AI model                                   |
| `/temperature <0.0-2.0>`  | Adjust temperature setting                            |
| `/system`                 | View or change system instructions                    |
| `/tokens`                 | Show token usage statistics                           |
| `/speed`                  | Show response time statistics                         |
| `/theme <theme>`          | Change the color theme (default, dark, light, hacker) |
| `/thinking`               | Show last AI thinking process                         |
| `/thinking-mode`          | Toggle thinking mode on/off                           |
| `/attach` or `/upload`    | Share a file with the AI                              |
| `/about`                  | Show information about OrChat                         |
| `/update`                 | Check for updates                                     |
| `/settings`               | View current settings                                 |

## 📁 File Attachment

Share files with the AI for analysis:

```
/attach path/to/your/file.ext
```

Supported file types:

- **Images**: JPG, PNG, GIF, WEBP (displayed visually with multimodal models)
- **Code Files**: Python, JavaScript, Java, C++, etc. (with syntax highlighting)
- **Text Documents**: TXT, MD, CSV (full content displayed)
- **Data Files**: JSON, XML (displayed with formatting)
- **PDFs and Archives**: Basic metadata support

## 🧠 Thinking Mode

OrChat can display the AI's reasoning process:

```
/thinking-mode       # Toggle thinking mode on/off
/thinking            # Show the most recent thinking process
```

This feature allows you to see how the AI approached your question before giving its final answer.

## 🔌 Plugin System

Extend OrChat's functionality with custom plugins by creating Python files in the `plugins` directory:

```python
from main import Plugin

class MyCustomPlugin(Plugin):
    def __init__(self):
        super().__init__("My Plugin", "Description of what my plugin does")

    def on_message(self, message, role):
        # Process message before sending/after receiving
        return message

    def on_command(self, command, args):
        # Handle custom commands
        if command == "my_command":
            return True, "Command executed successfully!"
        return False, "Command not handled"

    def get_commands(self):
        return ["/my_command - Description of my custom command"]
```

## 🎨 Themes

Change the visual appearance with the `/theme` command:

- **default**: Blue user, green assistant
- **dark**: Cyan user, magenta assistant
- **light**: Blue user, green assistant with lighter colors
- **hacker**: Matrix-inspired green text on black

## 📊 Token Management

OrChat intelligently manages conversation context to keep within token limits:

- Automatically trims old messages when approaching limits
- Displays token usage statistics after each response
- Allows manual clearing of context with `/clear`

## 🔄 Updates

Check for updates with the `/update` command to see if a newer version is available.

## 🔍 Troubleshooting

- **API Key Issues**: Ensure your OpenRouter API key is correctly set in config.ini or .env file
- **File Path Problems**: When using `/attach`, make sure to use the correct path format for your OS
- **Model Compatibility**: Some features like thinking mode only work with specific models

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) for providing unified API access to AI models
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal interface
