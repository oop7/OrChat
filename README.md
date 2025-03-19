# OrChat

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/oop7/OrChat/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)

A powerful CLI for chatting with AI models through OpenRouter with streaming responses, token tracking, and extensive customization options.

![OrChat Demo](https://raw.githubusercontent.com/oop7/OrChat/main/assets/demo.gif)

## ✨ Features

- **Universal Model Access**: Connect to any AI model available on OpenRouter
- **Interactive Chat**: Enjoy a smooth conversation experience with real-time streaming responses
- **Rich Markdown Rendering**: View formatted text, code blocks, tables and more directly in your terminal
- **Performance Analytics**: Track token usage and response times for cost efficiency
- **Multimodal Support**: Share images and various file types with compatible AI models
- **Extensible Plugin System**: Easily extend functionality with custom plugins
- **Multiple Export Formats**: Save conversations as Markdown, HTML, JSON, TXT, or PDF
- **Smart Context Management**: Automatically manages conversation history to stay within token limits
- **Customizable Themes**: Choose from different visual themes for your terminal
- **Code Execution**: Run generated code snippets directly from the chat interface

## 🚀 Installation

### From PyPI (Recommended)

```bash
pip install orchat
```

### From Source

```bash
git clone https://github.com/oop7/OrChat.git
pip install -r requirements.txt
cd orchat
python main.py
```

## 📋 Prerequisites

- Python 3.6 or higher
- An OpenRouter API key (get one at [OpenRouter.ai](https://openrouter.ai))

## 🏁 Getting Started

1. Install OrChat using one of the methods above
2. Run the setup wizard:
   ```bash
   orchat --setup
   ```
3. Enter your OpenRouter API key when prompted
4. Select your preferred AI model and configure settings
5. Start chatting!

## ⚙️ Configuration

OrChat can be configured in multiple ways:

1. **Setup Wizard**: Run `orchat --setup` for interactive configuration
2. **Config File**: Edit the `config.ini` file in the application directory
3. **Environment Variables**: Create a `.env` file with your configuration

Example `.env` file:
```
OPENROUTER_API_KEY=your_api_key_here
```

Example `config.ini` structure:
```ini
[API]
OPENROUTER_API_KEY = your_api_key_here

[SETTINGS]
MODEL = anthropic/claude-3-opus:beta
TEMPERATURE = 0.7
SYSTEM_INSTRUCTIONS = You are a helpful AI assistant.
THEME = default
MAX_TOKENS = 8000
AUTOSAVE_INTERVAL = 300
STREAMING = True
```

## 🖥️ Command-Line Options

- `--setup`: Run the setup wizard
- `--model MODEL`: Specify the model to use (e.g., `--model "anthropic/claude-3-opus:beta"`)
- `--task {creative,coding,analysis,chat}`: Optimize for a specific task type
- `--image PATH`: Analyze an image file

## 💬 Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/exit` or `/quit` | Exit the chat |
| `/new` | Start a new conversation |
| `/clear` | Clear conversation history |
| `/save [format]` | Save conversation (formats: md, html, json, txt, pdf) |
| `/model` | Change the AI model |
| `/temperature` | Adjust temperature setting (0.0-2.0) |
| `/system` | View or change system instructions |
| `/tokens` | Show token usage statistics |
| `/speed` | Show response time statistics |
| `/theme` | Change the color theme |
| `/thinking` | Show last AI thinking process |
| `/attach` or `/upload` | Share a file with the AI |
| `/execute` | Run code generated by the AI |
| `/about` | Show information about OrChat |
| `/update` | Check for updates |


## 🔌 Plugin System

Extend OrChat's functionality with custom plugins. Create Python files in the `plugins` directory that follow this structure:

```python
def register_plugin(chat_interface):
    # Register commands and hooks
    chat_interface.register_command("my_command", my_command_function)

def my_command_function(chat_interface, args):
    # Implement your command logic here
    pass
```

## 📊 Token Management

OrChat intelligently manages conversation context to keep within token limits:
- Automatically prunes old messages when approaching limits
- Displays token usage statistics after each response
- Allows manual clearing of context with `/clear`

## 🔄 Updates

Check for updates with the `/update` command or run:
```bash
pip install --upgrade orchat
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
