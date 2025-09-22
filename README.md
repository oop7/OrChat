<div align="center">

# 🤖 OrChat

<img src="assets\OrChat-Interface.png" width="800" alt="OrChat Interface"/>

[![PyPI version](https://img.shields.io/pypi/v/orchat?color=86efac&style=for-the-badge&logo=pypi&logoColor=black)](https://badge.fury.io/py/orchat)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge&logo=opensource&logoColor=white)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-10b981?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Downloads](https://img.shields.io/pepy/dt/orchat?color=1f2937&style=for-the-badge&logo=download&logoColor=white)](https://pepy.tech/project/orchat)
[![GitHub Stars](https://img.shields.io/github/stars/oop7/OrChat?color=86efac&style=for-the-badge&logo=github&logoColor=black)](https://github.com/oop7/OrChat/stargazers)

[🚀 Installation](#installation) • [✨ Features](#features) • [💬 Chat Commands](#chat-commands) • [🗂️ Conversation Management](#conversation-management) • [📁 File Attachment](#file-attachment) • [🧠 Thinking Mode](#thinking-mode) • [⚙️ Configuration](#configuration) • [🔍 Troubleshooting](#troubleshooting) • [🤝 Contributing](#contributing)

A powerful CLI for chatting with AI models through OpenRouter with streaming responses, token tracking, auto-update checking, multi-line input, conversation management with AI-generated summaries, and extensive customization options.

</div>


<a id="features"></a>
## ✨ Features

<details>
<summary><strong>🔗 Core Features</strong></summary>

- **Universal Model Access**: Connect to any AI model available on OpenRouter with dynamic model retrieval
- **Interactive Chat**: Enjoy a smooth conversation experience with real-time streaming responses
- **Rich Markdown Rendering**: View formatted text, code blocks, tables and more directly in your terminal
- **Performance Analytics**: Track token usage, response times, and total cost for efficiency monitoring (now with accurate API-based token counting)
- **Command Auto-completion**: Enhanced user experience with intelligent command suggestions and prompt history navigation
- **Prompt History Navigation**: Use ↑/↓ arrow keys to navigate through previous prompts and Ctrl+R for history search
- **Pricing Display**: Real-time pricing information displayed during active chat sessions
- **Auto-Update System**: Automatic update checking at startup with pip integration
- **Multi-line Input Support**: Compose multi-paragraph messages with `Esc+Enter` and visual feedback
- **Conversation Management**: Save, list, and resume conversations with AI-generated topic summaries
- **Smart Summarization**: Automatically generates meaningful names for saved sessions (e.g., "python_coding", "travel_advice")
- **Session Persistence**: Resume conversations exactly where you left off with full context

</details>

<details>
<summary><strong>📎 File & Media Support</strong></summary>

- **Smart File Picker**: Attach files anywhere in your message using `@` (e.g., `analyze @myfile.py`)
- **Interactive File Browser**: Browse files with icons, sizes, and directory navigation in a popup interface
- **Multimodal Support**: Share images and various file types with compatible AI models
- **Enhanced File Processing**: Improved file attachment with better error handling and path support

</details>

<details>
<summary><strong>🧠 Advanced Features</strong></summary>

- **Smart Thinking Mode**: See the AI's reasoning process with compatible models
- **Multiple Export Formats**: Save conversations as Markdown, HTML, JSON, TXT, or PDF
- **Smart Context Management**: Automatically manages conversation history to stay within token limits
- **Conversation Management**: Save, list, and resume conversations with AI-generated summaries
- **Customizable Themes**: Choose from different visual themes for your terminal

</details>

<details>
<summary><strong>⌨️ Interactive Input Features</strong></summary>

- **Multi-line Input**: Use `Esc+Enter` to toggle multi-line mode, with status indicator and seamless toggling
- **Command History Navigation**: Press ↑/↓ arrow keys to cycle through previous prompts and commands
- **History Search**: Use Ctrl+R to search through your prompt history with keywords
- **Automatic Command Completion**: Start typing "/" and command suggestions appear instantly - no Tab key needed!
- **Auto-Suggest from History**: Previous commands and prompts appear as grey suggestions as you type
- **Intelligent File Picker**: Use `@` anywhere in your message for file selection with auto-completion and browser popup
- **Double Ctrl+C Exit**: Press Ctrl+C twice within 2 seconds to gracefully exit the chat session

**💡 How Auto-Completion Works:**
- Type `/` → All available commands appear automatically
- Type `/c` → Filters to commands starting with 'c' (clear, cls, clear-screen, etc.)
- Type `/temp` → Shows `/temperature` command
- Type `/think` → Shows `/thinking` and `/thinking-mode` commands
- No Tab key required - completions appear as you type!

**💡 How File Picker Works:**
- Type `@` anywhere in your message to open the file picker
- Choose files interactively (with icons for file types)
- Insert filenames naturally into your prompt, e.g., `examine @test.py and check for errors`
- File picker works anywhere in your message, not just at the beginning

**💡 How to Exit:**
- Press **Ctrl+C** once → Shows "Press Ctrl+C again to exit" message
- Press **Ctrl+C** again within 2 seconds → Gracefully exits the chat
- This prevents accidental exits while allowing quick termination when needed

</details>

<a id="installation"></a>
## 🚀 Installation

<summary><strong>📦 Installation Methods</strong></summary>

### From PyPI (Recommended)

```bash
pip install orchat
```
```bash
# Run the application
orchat
```

### From Source

```bash
git clone https://github.com/oop7/OrChat.git
pip install -r requirements.txt
python main.py
```

</details>

</details>

<details>
<summary><strong>📋 Prerequisites</strong></summary>

- Python 3.7 or higher
- An OpenRouter API key (get one at [OpenRouter.ai](https://openrouter.ai))
- Required packages: in `requirements.txt`

</details>

<details>
<summary><strong>🏁 Getting Started</strong></summary>

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

</details>

<details>
<summary><strong>🪛 Add-Ons</strong></summary>

### FZF fuzzy search (Enhanced Model Selection)

1. Install fzf and pyfzf

   - Install pyfzf
     ```bash
     pip install pyfzf
     ```
   - Fzf can be downloaded from https://github.com/junegunn/fzf?tab=readme-ov-file#installation

2. Ensure fzf is in your path
3. From now on, the model selection will use fzf for powerful fuzzy search and filtering capabilities!

**Note**: If fzf is not installed, OrChat will automatically fall back to standard model selection.

</details>

<a id="configuration"></a>
## ⚙️ Configuration

<details>
<summary><strong>🔧 Configuration Methods</strong></summary>

OrChat can be configured in multiple ways:

1. **Setup Wizard**: Run `python main.py --setup` for interactive configuration
2. **Config File**: Edit the `config.ini` file in the application directory
3. **Environment Variables**: Create a `.env` file with your configuration
4. **System Environment Variables**: Set environment variables directly in your system (recommended for security)

**Enhanced Environment Support**: OrChat now supports system/user environment variables, removing the strict requirement for `.env` files.

</details>

<details>
<summary><strong>📄 Configuration Examples</strong></summary>

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
THINKING_MODE = False
```

</details>

<details>
<summary><strong>🖥️ Command-Line Options</strong></summary>

- `--setup`: Run the setup wizard
- `--model MODEL`: Specify the model to use (e.g., `--model "anthropic/claude-3-opus"`)
- `--task {creative,coding,analysis,chat}`: Optimize for a specific task type
- `--image PATH`: Analyze an image file

</details>

<a id="chat-commands"></a>
## 💬 Chat Commands

| Command                   | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `/help`                   | Show available commands                               |
| `/new`                    | Start a new conversation                              |
| `/clear`                  | Clear conversation history                            |
| `/cls` or `/clear-screen` | Clear the terminal screen                             |
| `/save [format]`          | Save conversation (formats: md, html, json, txt, pdf) |
| `/chat list`              | List saved conversations with human-readable summaries |
| `/chat save`              | Save current conversation with auto-generated summary  |
| `/chat resume <session>`  | Resume a saved conversation by name or ID              |
| `/model`                  | Change the AI model                                   |
| `/temperature <0.0-2.0>`  | Adjust temperature setting                            |
| `/system`                 | View or change system instructions                    |
| `/tokens`                 | Show token usage statistics (now API-accurate)        |
| `/speed`                  | Show response time statistics                         |
| `/theme <theme>`          | Change the color theme (default, dark, light, hacker) |
| `/thinking`               | Show last AI thinking process                         |
| `/thinking-mode`          | Toggle thinking mode on/off                           |
| `/about`                  | Show information about OrChat                         |
| `/update`                 | Check for updates                                     |
| `/settings`               | View current settings                                 |
| **Ctrl+C** (twice)        | **Exit the chat (press twice within 2 seconds)**     |

<a id="conversation-management"></a>
## 💾 Conversation Management

<details>
<summary><strong>📋 Session Management</strong></summary>

OrChat provides powerful conversation management with human-readable session summaries:

**Commands:**
- `/chat list` - View all saved conversations with meaningful names
- `/chat save` - Save current conversation with auto-generated topic summary
- `/chat resume <session>` - Resume any saved conversation by name or ID

**Features:**
- **Smart Summarization**: Uses AI to generate 2-4 word topic summaries (e.g., "python_coding", "travel_advice", "cooking_tips")
- **Fallback Detection**: Automatically detects topics like coding, travel, cooking, career advice
- **Dual Storage**: Saves both human-readable summaries and original timestamp IDs
- **Easy Resume**: Resume conversations using either the summary name or original ID

**Example Session List:**
```
Saved sessions:
general_chat (20250906_141133)
python_coding (20250906_140945)
travel_advice (20250906_140812)
cooking_tips (20250906_140734)
```

</details>

<a id="file-attachment"></a>
## 📁 File Attachment

<details>
<summary><strong>📎 Basic Usage</strong></summary>

Attach files naturally in your messages using the smart file picker:

```
analyze @path/to/your/file.ext for issues
examine @script.py and explain its logic
```
- Use `@` anywhere in your message to open the file picker popup

</details>

<details>
<summary><strong>✨ Enhanced Features</strong></summary>

- **Intelligent File Picker**: Auto-completion, icons, file sizes, and directory navigation
- **Quoted Path Support**: Handles file paths with spaces using quotes
- **Better Error Handling**: Improved error messages and usage examples
- **File Preview**: Shows file metadata and preview before processing
- **Security Validation**: Built-in file size and type validation (10MB limit)

</details>

<details>
<summary><strong>📋 Supported File Types</strong></summary>

- **Images**: JPG, PNG, GIF, WEBP, BMP (displayed visually with multimodal models)
- **Code Files**: Python, JavaScript, Java, C++, TypeScript, Swift, etc. (with syntax highlighting)
- **Text Documents**: TXT, MD, CSV (full content displayed)
- **Data Files**: JSON, XML (displayed with formatting)
- **Web Files**: HTML, CSS (formatted display)
- **Archives**: ZIP, TAR, GZ, RAR (basic metadata support)

</details>

<a id="thinking-mode"></a>
## 🧠 Thinking Mode

<details>
<summary><strong>🎯 Basic Usage</strong></summary>

OrChat can display the AI's reasoning process with enhanced thinking mode:

```
/thinking-mode       # Toggle thinking mode on/off
/thinking            # Show the most recent thinking process
```

This feature allows you to see how the AI approached your question before giving its final answer. **Auto Thinking Mode** automatically enables this feature when you select models with reasoning support.

</details>

<details>
<summary><strong>✨ Enhanced Features</strong></summary>

- **Improved Detection**: Better extraction of thinking content from model responses
- **Model Compatibility**: Automatic handling of models that don't support thinking mode
- **Visual Indicators**: Clear status indicators showing if thinking mode is enabled
- **Flexible Setup**: Option to enable/disable during model selection

</details>

## 🎨 Themes

<details>
<summary><strong>🎨 Available Themes</strong></summary>

Change the visual appearance with the `/theme` command:

- **default**: Blue user, green assistant
- **dark**: Cyan user, magenta assistant
- **light**: Blue user, green assistant with lighter colors
- **hacker**: Matrix-inspired green text on black

</details>

## 📊 Token Management

<details>
<summary><strong>📊 Smart Context Management</strong></summary>

OrChat intelligently manages conversation context to keep within token limits:

- Automatically trims old messages when approaching limits
- Displays comprehensive token usage statistics including total tokens and cost tracking
- Shows real-time pricing information during active sessions
- Displays total cost tracking across conversations
- Allows manual clearing of context with `/clear`

</details>

## 🔄 Updates

<details>
<summary><strong>🔄 Version Management</strong></summary>

Check for updates with the `/update` command to see if a newer version is available.

</details>



<a id="troubleshooting"></a>
## 🔍 Troubleshooting

<details>
<summary><strong>🔍 Common Issues & Solutions</strong></summary>

- **API Key Issues**: Ensure your OpenRouter API key is correctly set in config.ini, .env file, or system environment variables. OrChat will prompt for re-entry if an incorrect key is detected
- **Insufficient Account Credit**: If you receive a 402 error, check your OpenRouter account balance and add funds as needed
- **File Path Problems**: When using `/attach` or `/upload`, use quotes for paths with spaces and ensure correct path format for your OS
- **Model Compatibility**: Some features like thinking mode only work with specific models
- **Conversation Management**: Use `/chat list` to see saved conversations, `/chat save` to save current session, and `/chat resume <name>` to continue previous conversations
- **Command Usage**: Remember that `/upload` and `/attach` can be used anywhere in your message for flexibility

</details>

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<a id="contributing"></a>
## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 🙏 Acknowledgments

<details>
<summary><strong>🙏 Special Thanks</strong></summary>

- [OpenRouter](https://openrouter.ai/) for providing unified API access to AI models
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal interface
- All contributors and users who provide feedback and help improve OrChat

</details>

