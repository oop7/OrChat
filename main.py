import json
import os
import time
import argparse
import sys
import configparser
import datetime
import tempfile
import subprocess
import re
import importlib.util
import base64
import webbrowser
import urllib.request
from collections import Counter

import colorama
import requests
import tiktoken
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from packaging import version
#from colorama import Fore, Style
#from rich.markdown import Markdown
#from rich.progress import Progress
#from rich.syntax import Syntax

try:
    from pyfzf.pyfzf import FzfPrompt
    HAS_FZF=True
except ImportError:
    HAS_FZF=False

# Initialize colorama for cross-platform colored terminal output
colorama.init()

# Initialize Rich console
console = Console()

# Constants for the application
APP_NAME = "OrChat"
APP_VERSION = "1.2.1"
REPO_URL = "https://github.com/oop7/OrChat"
API_URL = "https://api.github.com/repos/oop7/OrChat/releases/latest"

# Add a new global variable at the top of the file
last_thinking_content = ""

def load_config():
    """Load configuration from .env file and/or config.ini"""
    # First try to load from .env file
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Then try config.ini (overrides .env if both exist)
    config = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')

    if os.path.exists(config_file):
        config.read(config_file)
        if 'API' in config and 'OPENROUTER_API_KEY' in config['API']:
            if config['API']['OPENROUTER_API_KEY']:
                api_key = config['API']['OPENROUTER_API_KEY']

        # Load other settings if available
        if 'SETTINGS' in config:
            settings = config['SETTINGS']
            return {
                'api_key': api_key,
                'model': settings.get('MODEL', ""),
                'temperature': settings.getfloat('TEMPERATURE', 0.7),
                'system_instructions': settings.get('SYSTEM_INSTRUCTIONS', ""),
                'theme': settings.get('THEME', 'default'),
                'max_tokens': settings.getint('MAX_TOKENS', 8000),
                'autosave_interval': settings.getint('AUTOSAVE_INTERVAL', 300),
                'streaming': settings.getboolean('STREAMING', True),
                'thinking_mode': settings.getboolean('THINKING_MODE', False)  # Changed default to False
            }

    # Return defaults if no config file
    return {
        'api_key': api_key,
        'model': "",
        'temperature': 0.7,
        'system_instructions': "",
        'theme': 'default',
        'max_tokens': 8000,
        'autosave_interval': 300,
        'streaming': True,
        'thinking_mode': False  # Changed default to False
    }

def save_config(config_data):
    """Save configuration to config.ini file"""
    config = configparser.ConfigParser()
    if 'OPENROUTER_API_KEY' not in os.environ:
        config['API'] = {'OPENROUTER_API_KEY': config_data['api_key']}
    config['SETTINGS'] = {
        'MODEL': config_data['model'],
        'TEMPERATURE': str(config_data['temperature']),
        'SYSTEM_INSTRUCTIONS': config_data['system_instructions'],
        'THEME': config_data['theme'],
        'MAX_TOKENS': str(config_data['max_tokens']),
        'AUTOSAVE_INTERVAL': str(config_data['autosave_interval']),
        'STREAMING': str(config_data['streaming']),
        'THINKING_MODE': str(config_data['thinking_mode'])  # Add this line
    }

    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    with open(config_file, 'w', encoding="utf-8") as f:
        config.write(f)
    console.print("[green]Configuration saved successfully![/green]")

def count_tokens(text, model_name="cl100k_base"):
    """Counts the number of tokens in a given text string using tiktoken."""
    try:
        encoding = tiktoken.get_encoding(model_name)
    except KeyError:
        console.print(f"[yellow]Warning: Model encoding {model_name} not found. Using cl100k_base as default[/yellow]")
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    return len(tokens)

def get_available_models():
    """Fetch available models from OpenRouter API"""
    try:
        config = load_config()
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        with console.status("[bold green]Fetching available models..."):
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)

        if response.status_code == 200:
            models_data = response.json()
            return models_data["data"]
        console.print(f"[red]Error fetching models: {response.status_code}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Error fetching models: {str(e)}[/red]")
        return []

def select_model(config):
    """Simplified model selection interface"""
    all_models = get_available_models()

    if not all_models:
        console.print("[red]No models available. Please check your API key and internet connection.[/red]")
        return None

    # Option to directly enter a model name
    console.print("[bold green]Model Selection[/bold green]")
    console.print("\n[bold magenta]Options:[/bold magenta]")
    console.print("[bold]1[/bold] - View all available models")
    console.print("[bold]2[/bold] - Show free models only")
    console.print("[bold]3[/bold] - Enter model name directly")
    console.print("[bold]q[/bold] - Cancel selection")

    choice = Prompt.ask("Select an option", choices=["1", "2", "3", "q"], default="1")

    if choice == "q":
        return None

    elif choice == "3":
        # Direct model name entry
        console.print("[yellow]Enter the exact model name (e.g., 'anthropic/claude-3-opus')[/yellow]")
        model_name = Prompt.ask("Model name")

        # Validate the model name
        model_exists = any(model["id"] == model_name for model in all_models)
        if model_exists:
            # Ask about thinking mode support
            try:
                prompt_for_thinking_mode(config)
            except Exception as e:
                console.print(f"[yellow]Error setting thinking mode: {str(e)}. Using default settings.[/yellow]")
            return model_name

        console.print("[yellow]Warning: Model not found in available models. Using anyway.[/yellow]")
        confirm = Prompt.ask("Continue with this model name? (y/n)", default="y")
        if confirm.lower() == "y":
            # Ask about thinking mode support
            try:
                prompt_for_thinking_mode(config)
            except Exception as e:
                console.print(f"[yellow]Error setting thinking mode: {str(e)}. Using default settings.[/yellow]")
            return model_name
        return select_model(config)  # Start over

    elif choice == "1":
        # All models, simple numbered list
        console.print("[bold green]All Available Models:[/bold green]")

        if HAS_FZF:
            fzf = FzfPrompt()
            model_choice = fzf.prompt([ model['id']  for  model in all_models ])
            if not model_choice:
                console.print("[red]No model selected. Exiting...[/red]")
                return select_model(config)
            else:
                try:
                    prompt_for_thinking_mode(config)
                except Exception as e:
                    console.print(f"[yellow]Error setting thinking mode: {str(e)}. Using default settings.[/yellow]")
                return model_choice[0]

        with console.pager(styles=True):
            for i, model in enumerate(all_models, 1):
                # Highlight free models
                if model['id'].endswith(":free"):
                    console.print(f"[bold]{i}.[/bold] {model['id']} [green](FREE)[/green]")
                else:
                    console.print(f"[bold]{i}.[/bold] {model['id']}")

        model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")

        if model_choice.lower() == 'b':
            return select_model(config)

        try:
            index = int(model_choice) - 1
            if 0 <= index < len(all_models):
                selected_model = all_models[index]['id']
                # Ask about thinking mode support
                try:
                    prompt_for_thinking_mode(config)
                except Exception as e:
                    console.print(f"[yellow]Error setting thinking mode: {str(e)}. Using default settings.[/yellow]")
                return selected_model
            else:
                console.print("[red]Invalid selection[/red]")
                return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            return select_model(config)

    elif choice == "2":
        # Show only free models
        free_models = [model for model in all_models if model['id'].endswith(":free")]

        if not free_models:
            console.print("[yellow]No free models found.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)

        console.print("[bold green]Free Models:[/bold green]")
        for i, model in enumerate(free_models, 1):
            console.print(f"[bold]{i}.[/bold] {model['id']} [green](FREE)[/green]")

        model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")

        if model_choice.lower() == 'b':
            return select_model(config)

        try:
            index = int(model_choice) - 1
            if 0 <= index < len(free_models):
                selected_model = free_models[index]['id']
                # Ask about thinking mode support
                try:
                    prompt_for_thinking_mode(config)
                except Exception as e:
                    console.print(f"[yellow]Error setting thinking mode: {str(e)}. Using default settings.[/yellow]")
                return selected_model
            console.print("[red]Invalid selection[/red]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)

def prompt_for_thinking_mode(config):
    """Ask if the selected model supports thinking mode"""
    console.print("[yellow]Some models support showing AI reasoning with <thinking></thinking> tags.[/yellow]")
    thinking_support = Prompt.ask(
        "Do you know if this model supports thinking mode?",
        choices=["y", "n", "unknown"],
        default="n"  # Changed from unknown to n
    )

    # Make sure the thinking_mode key exists in config
    if 'thinking_mode' not in config:
        config['thinking_mode'] = False  # Default to disabled

    if thinking_support.lower() == "y":
        config['thinking_mode'] = True
        console.print("[green]Thinking mode enabled for this model.[/green]")
    elif thinking_support.lower() == "n":
        config['thinking_mode'] = False
        console.print("[yellow]Thinking mode disabled for this model.[/yellow]")
    else:
        # For unknown, keep the current setting
        console.print(f"[yellow]Keeping current thinking mode setting: {'enabled' if config['thinking_mode'] else 'disabled'}[/yellow]")
        console.print("[dim]You can toggle this setting anytime with /thinking-mode[/dim]")

    # Don't save the config during model selection - just update the thinking_mode value
    # The calling function will handle saving when all settings are complete

def setup_wizard():
    """Interactive setup wizard for first-time users"""
    console.print(Panel.fit(
        "[bold blue]Welcome to the OrChat Setup Wizard![/bold blue]\n"
        "Let's configure your chat settings.",
        title="Setup Wizard"
    ))

    if "OPENROUTER_API_KEY" not in os.environ:
        api_key = Prompt.ask("Enter your OpenRouter API key")
    else:
        api_key = os.getenv("OPENROUTER_API_KEY")

    # Save API key temporarily to allow model fetching
    temp_config = {'api_key': api_key, 'thinking_mode': False}  # Default to disabled

    # Use the simplified model selection
    console.print("[bold]Select an AI model to use:[/bold]")
    model = ""
    thinking_mode = False  # Default value - disabled
    try:
        with console.status("[bold green]Connecting to OpenRouter...[/bold green]"):
            # Small delay to ensure the API key is registered
            time.sleep(1)

        selected_model = select_model(temp_config)
        if selected_model:
            model = selected_model
            # Use the thinking_mode value that was set during model selection
            thinking_mode = temp_config.get('thinking_mode', False)
        else:
            console.print("[yellow]Model selection cancelled. You can set a model later.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Error during model selection: {str(e)}. You can set a model later.[/yellow]")

    temperature = float(Prompt.ask("Set temperature (0.0-2.0)", default="0.7"))
    if temperature > 1.0:
        console.print("[yellow]Warning: High temperature values (>1.0) may cause erratic or nonsensical responses.[/yellow]")
        confirm = Prompt.ask("Are you sure you want to use this high temperature? (y/n)", default="n")
        if confirm.lower() != 'y':
            temperature = float(Prompt.ask("Enter a new temperature value (0.0-1.0)", default="0.7"))

    console.print("[bold]Enter system instructions (guide the AI's behavior)[/bold]")
    console.print("[dim]Press Enter twice to finish[/dim]")
    lines = []
    empty_line_count = 0
    while True:
        line = input()
        if not line:
            empty_line_count += 1
            if empty_line_count >= 2:  # Exit after two consecutive empty lines
                break
        else:
            empty_line_count = 0  # Reset counter if non-empty line
            lines.append(line)

    # If no instructions provided, use a default value
    if not lines:
        system_instructions = "You are a helpful AI assistant."
        console.print("[yellow]No system instructions provided. Using default instructions.[/yellow]")
    else:
        system_instructions = "\n".join(lines)

    # Add theme selection
    available_themes = ['default', 'dark', 'light', 'hacker']
    console.print("[green]Available themes:[/green]")
    for theme in available_themes:
        console.print(f"- {theme}")
    theme_choice = Prompt.ask("Select theme", choices=available_themes, default="default")

    # We already asked about thinking mode during model selection, so we'll use that value
    # Only ask if model selection failed or was cancelled
    if not model:
        # Enhanced thinking mode explanation
        console.print(Panel.fit(
            "[yellow]Thinking Mode:[/yellow]\n\n"
            "Thinking mode shows the AI's reasoning process between <thinking> and </thinking> tags.\n"
            "This reveals how the AI approaches your questions and can help you understand its thought process.\n\n"
            "[dim]Note: Not all models support this feature. If you notice issues with responses, you can disable it later with /thinking-mode[/dim]",
            title="🧠 AI Reasoning Process",
            border_style="yellow"
        ))

        thinking_mode = Prompt.ask(
            "Enable thinking mode?",
            choices=["y", "n"],
            default="n"
        ).lower() == "y"

    config_data = {
        'api_key': api_key,
        'model': model,
        'temperature': temperature,
        'system_instructions': system_instructions,
        'theme': theme_choice,
        'max_tokens': 8000,
        'autosave_interval': 300,
        'streaming': True,
        'thinking_mode': thinking_mode
    }

    save_config(config_data)
    return config_data

def format_time_delta(delta_seconds):
    """Format time delta in a human-readable format"""
    if delta_seconds < 1:
        return f"{delta_seconds*1000:.0f}ms"
    elif delta_seconds < 60:
        return f"{delta_seconds:.2f}s"
    else:
        minutes = int(delta_seconds // 60)
        seconds = delta_seconds % 60
        return f"{minutes}m {seconds:.2f}s"

def format_file_size(size_bytes):
    """Format file size in a human-readable way"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def stream_response(response, start_time, thinking_mode=False):
    """Stream the response from the API with proper text formatting"""
    console.print("\n[bold green]Assistant[/bold green]")

    # Full content accumulates everything
    full_content = ""
    # For thinking detection
    thinking_content = ""
    in_thinking = False

    # Create a temporary file to collect all content
    # This avoids terminal display issues
    collected_content = []

    # For debugging purposes
    global last_thinking_content

    try:
        for chunk in response.iter_lines():
            if not chunk:
                continue

            chunk_text = chunk.decode('utf-8', errors='replace')

            if "OPENROUTER PROCESSING" in chunk_text:
                continue

            if chunk_text.startswith('data:'):
                chunk_text = chunk_text[5:].strip()

            if chunk_text == "[DONE]":
                continue

            try:
                chunk_data = json.loads(chunk_text)
                if 'choices' in chunk_data and chunk_data['choices']:
                    delta = chunk_data['choices'][0].get('delta', {})
                    content = delta.get('content', delta.get('text', ''))

                    if content:
                        # Add to full content
                        full_content += content

                        # Only process thinking tags if thinking mode is enabled
                        if thinking_mode:
                            # Check for thinking tags
                            if "<thinking>" in content:
                                in_thinking = True
                                # Extract content after the tag
                                thinking_part = content.split("<thinking>", 1)[1]
                                thinking_content += thinking_part
                                # Skip this chunk - don't display the <thinking> tag
                                continue

                            if "</thinking>" in content:
                                in_thinking = False
                                # Extract content before the tag
                                thinking_part = content.split("</thinking>", 1)[0]
                                thinking_content += thinking_part
                                # Skip this chunk - don't display the </thinking> tag
                                continue

                            if in_thinking:
                                thinking_content += content
                                continue

                        # Not in thinking mode or model doesn't support thinking, collect for display
                        collected_content.append(content)
            except json.JSONDecodeError:
                # For non-JSON chunks, quietly ignore
                pass
    except Exception as e:
        console.print(f"\n[red]Error during streaming: {str(e)}[/red]")

    # Now display the collected content all at once
    # This avoids the vertical text issue
    if collected_content:
        print("".join(collected_content))
    else:
        # If we only got thinking content, display a default response
        print("Hello! I'm here to help you.")

    # More robust thinking extraction - uses regex pattern to look for any thinking tags in the full content
    thinking_section = ""
    thinking_pattern = re.compile(r'<thinking>(.*?)</thinking>', re.DOTALL)
    thinking_matches = thinking_pattern.findall(full_content)

    if thinking_mode and thinking_matches:
        thinking_section = "\n".join(thinking_matches)
        # Update the global thinking content variable
        last_thinking_content = thinking_section

        # Display thinking content immediately if found
        console.print(Panel.fit(
            last_thinking_content,
            title="🧠 AI Thinking Process",
            border_style="yellow"
        ))
    else:
        # Also check if thinking_content has any content from our incremental collection
        if thinking_content.strip():
            last_thinking_content = thinking_content

            # Display thinking content immediately if found
            console.print(Panel.fit(
                last_thinking_content,
                title="🧠 AI Thinking Process",
                border_style="yellow"
            ))

    # Clean the full content - only if model supports thinking
    cleaned_content = full_content
    if thinking_mode and "<thinking>" in full_content:
        # Remove the thinking sections with a more robust pattern
        try:
            # Use a non-greedy match to handle multiple thinking sections
            cleaned_content = re.sub(r'<thinking>.*?</thinking>', '', full_content, flags=re.DOTALL)
            cleaned_content = cleaned_content.strip()
        except:
            # Fallback to simpler method
            parts = full_content.split("</thinking>")
            if len(parts) > 1:
                cleaned_content = parts[-1].strip()

    # If after cleaning we have nothing, use a default response
    if not cleaned_content.strip():
        cleaned_content = "Hello! I'm here to help you."

    response_time = time.time() - start_time
    return cleaned_content, response_time

def save_conversation(conversation_history, filename, fmt="markdown"):
    """Save conversation to file in various formats"""
    if fmt == "markdown":
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("# OrChat Conversation\n\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for msg in conversation_history:
                if msg['role'] == 'system':
                    f.write(f"## System Instructions\n\n{msg['content']}\n\n")
                else:
                    f.write(f"## {msg['role'].capitalize()}\n\n{msg['content']}\n\n")
    elif fmt == "json":
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(conversation_history, f, indent=2)
    elif fmt == "html":
        with open(filename, 'w', encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n")
            f.write("<title>OrChat Conversation</title>\n")
            f.write("<style>\n")
            f.write("body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }\n")
            f.write(".system { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }\n")
            f.write(".user { background-color: #e1f5fe; padding: 10px; border-radius: 5px; margin: 10px 0; }\n")
            f.write(".assistant { background-color: #f1f8e9; padding: 10px; border-radius: 5px; margin: 10px 0; }\n")
            f.write("</style>\n</head>\n<body>\n")
            f.write("<h1>OrChat Conversation</h1>\n")
            f.write(f"<p>Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n")

            for msg in conversation_history:
                f.write(f"<div class='{msg['role']}'>\n")
                f.write(f"<h2>{msg['role'].capitalize()}</h2>\n")
                content_html = msg['content'].replace('\n', '<br>')
                f.write(f"<p>{content_html}</p>\n")
                f.write("</div>\n")

            f.write("</body>\n</html>")

    return filename

def manage_context_window(conversation_history, max_tokens=8000, model_name="cl100k_base"):
    """Manage the context window to prevent exceeding token limits"""
    # Always keep the system message
    system_message = conversation_history[0]

    # Count total tokens in the conversation
    total_tokens = sum(count_tokens(msg["content"], model_name) for msg in conversation_history)

    # If we're under the limit, no need to trim
    if total_tokens <= max_tokens:
        return conversation_history, 0

    # We need to trim the conversation
    # Start with just the system message
    trimmed_history = [system_message]
    current_tokens = count_tokens(system_message["content"], model_name)

    # Add messages from the end (most recent) until we approach the limit
    # Leave room for the next user message
    messages_to_consider = conversation_history[1:]
    trimmed_count = 0

    for msg in reversed(messages_to_consider):
        msg_tokens = count_tokens(msg["content"], model_name)
        if current_tokens + msg_tokens < max_tokens - 1000:  # Leave 1000 tokens buffer
            trimmed_history.insert(1, msg)  # Insert after system message
            current_tokens += msg_tokens
        else:
            trimmed_count += 1

    # Add a note about trimmed messages if any were removed
    if trimmed_count > 0:
        note = {"role": "system", "content": f"Note: {trimmed_count} earlier messages have been removed to stay within the context window."}
        trimmed_history.insert(1, note)

    return trimmed_history, trimmed_count

def process_file_upload(file_path, conversation_history):
    """Process a file upload and add its contents to the conversation"""
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read()

        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        # Determine file type and create appropriate message
        if file_ext in ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.ts', '.swift']:
            file_type = "code"
            message = f"I'm uploading a code file named '{file_name}'. Please analyze it:\n\n```{file_ext[1:]}\n{content}\n```"
        elif file_ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css']:
            file_type = "text"
            message = f"I'm uploading a text file named '{file_name}'. Here are its contents:\n\n{content}"
        else:
            file_type = "unknown"
            message = f"I'm uploading a file named '{file_name}'. Here are its contents:\n\n{content}"

        # Add to conversation history
        conversation_history.append({"role": "user", "content": message})
        return True, f"File '{file_name}' uploaded successfully as {file_type}."
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def handle_attachment(file_path, conversation_history):
    """Enhanced file attachment handling with preview and metadata"""
    try:
        # Get file information
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        file_size_formatted = format_file_size(file_size)

        # Determine file type and create appropriate message
        file_type, content = extract_file_content(file_path, file_ext)

        # Create a message that includes metadata about the attachment
        message = f"I'm sharing a file: **{file_name}** ({file_type}, {file_size_formatted})\n\n"

        if file_type == "image":
            # For images, we'll use the multimodal API format
            with open(file_path, 'rb', encoding='utf-8') as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')

            # Add to messages with proper format for multimodal models
            conversation_history.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": f"data:image/{file_ext[1:]};base64,{base64_image}"}}
                ]
            })
            return True, f"Image '{file_name}' attached successfully."
        else:
            # For other file types, add content to the message
            message += content
            conversation_history.append({"role": "user", "content": message})
            return True, f"File '{file_name}' attached successfully as {file_type}."

    except Exception as e:
        return False, f"Error processing attachment: {str(e)}"

def extract_file_content(file_path, file_ext):
    """Extract and format content from different file types"""
    # Determine file type based on extension
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
        return "image", ""

    elif file_ext in ['.pdf']:
        # Basic PDF handling - just mention it's a PDF
        return "PDF document", "[PDF content not displayed in chat, but AI can analyze the document]"

    elif file_ext in ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.ts', '.swift']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "code", f"```{file_ext[1:]}\n{content}\n```"

    elif file_ext in ['.txt', '.md', '.csv']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "text", content

    elif file_ext in ['.json', '.xml']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "data", f"```{file_ext[1:]}\n{content}\n```"

    elif file_ext in ['.html', '.css']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return "web", f"```{file_ext[1:]}\n{content}\n```"

    elif file_ext in ['.zip', '.tar', '.gz', '.rar']:
        return "archive", "[Archive content not displayed in chat]"

    else:
        # Try to read as text, but handle binary files
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return "unknown", content
        except:
            return "binary", "[Binary content not displayed in chat]"

def execute_code(code_block, language):
    """Execute a code block and return the result"""
    if language not in ['python']:
        return False, f"Code execution not supported for {language}"

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{language}', delete=False) as temp:
            temp_name = temp.name
            temp.write(code_block.encode('utf-8'))

        # Execute the code
        if language == 'python':
            result = subprocess.run(
                [sys.executable, temp_name],
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout for safety
            )

            # Clean up
            os.unlink(temp_name)

            if result.returncode == 0:
                return True, f"Code executed successfully:\n\n```\n{result.stdout}\n```"
            else:
                return False, f"Code execution failed:\n\n```\n{result.stderr}\n```"
    except Exception as e:
        return False, f"Error executing code: {str(e)}"

def apply_theme(theme_name):
    """Apply a color theme to the console"""
    themes = {
        'default': {
            'user_color': 'blue',
            'assistant_color': 'green',
            'system_color': 'yellow',
            'error_color': 'red',
            'panel_border': 'green',
            'panel_title': 'white'
        },
        'dark': {
            'user_color': 'cyan',
            'assistant_color': 'magenta',
            'system_color': 'yellow',
            'error_color': 'red',
            'panel_border': 'cyan',
            'panel_title': 'white'
        },
        'light': {
            'user_color': 'blue',
            'assistant_color': 'green',
            'system_color': 'yellow',
            'error_color': 'red',
            'panel_border': 'blue',
            'panel_title': 'black'
        },
        'hacker': {
            'user_color': 'green',
            'assistant_color': 'green',
            'system_color': 'green',
            'error_color': 'red',
            'panel_border': 'green',
            'panel_title': 'green'
        }
    }

    return themes.get(theme_name, themes['default'])

class Plugin:
    """Base class for plugins"""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def on_load(self):
        """Called when the plugin is loaded"""
        pass

    def on_message(self, message, role):
        """Called when a message is sent or received"""
        return message

    def on_command(self, command, args):
        """Called when a command is executed"""
        return False, "Command not handled by plugin"

    def get_commands(self):
        """Return a list of commands this plugin provides"""
        return []

def load_plugins():
    """Load plugins from the plugins directory"""
    plugins = []
    plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")

    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
        return plugins

    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                module_name = filename[:-3]
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    os.path.join(plugins_dir, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for Plugin subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, Plugin) and
                        attr is not Plugin):
                        plugin = attr()
                        plugin.on_load()
                        plugins.append(plugin)
                        console.print(f"[green]Loaded plugin: {plugin.name}[/green]")
            except Exception as e:
                console.print(f"[red]Error loading plugin {filename}: {str(e)}[/red]")

    return plugins

def optimize_streaming():
    """Configure optimized streaming for better performance"""
    # Set chunk size optimization
    chunk_size = 1024

    # Configure adaptive timeouts
    base_timeout = 30
    per_token_timeout = 0.01

    # Enable resilient reconnection
    max_retries = 3
    retry_delay = 1

    return {
        "chunk_size": chunk_size,
        "timeout": {
            "base": base_timeout,
            "per_token": per_token_timeout,
            "max": 120
        },
        "retry": {
            "max": max_retries,
            "delay": retry_delay
        }
    }

# Add this function to show about information
def show_about():
    """Display information about OrChat"""
    console.print(Panel.fit(
        f"[bold blue]Or[/bold blue][bold green]Chat[/bold green] [dim]v{APP_VERSION}[/dim]\n\n"
        "A powerful CLI for chatting with AI models through OpenRouter.\n\n"
        f"[link={REPO_URL}]{REPO_URL}[/link]\n\n"
        "Created by OOP7\n"
        "Licensed under MIT License",
        title="ℹ️ About OrChat",
        border_style="blue"
    ))

# Add this function to check for updates
def check_for_updates():
    """Check GitHub for newer versions of OrChat"""
    console.print("[bold cyan]Checking for updates...[/bold cyan]")
    try:
        with urllib.request.urlopen(API_URL) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', 'v0.0.0').lstrip('v')

                if version.parse(latest_version) > version.parse(APP_VERSION):
                    console.print(Panel.fit(
                        f"[yellow]A new version of OrChat is available![/yellow]\n"
                        f"Current version: [cyan]{APP_VERSION}[/cyan]\n"
                        f"Latest version: [green]{latest_version}[/green]\n\n"
                        f"Update at: {REPO_URL}/releases",
                        title="📢 Update Available",
                        border_style="yellow"
                    ))

                    open_browser = Prompt.ask("Open release page in browser?", choices=["y", "n"], default="n")
                    if open_browser.lower() == "y":
                        webbrowser.open(f"{REPO_URL}/releases")
                else:
                    console.print("[green]You are using the latest version of OrChat![/green]")
            else:
                console.print("[yellow]Could not check for updates. Server returned status "
                            f"code {response.getcode()}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Could not check for updates: {str(e)}[/yellow]")

def model_supports_thinking(model_id):
    """Determine if a model properly supports the thinking tag format"""
    # Instead of a hardcoded list, ask the user if they know their model supports thinking
    console.print("[yellow]Note: Some models support showing thinking processes with <thinking></thinking> tags.[/yellow]")
    enable_thinking = Prompt.ask(
        "Do you know if this model supports thinking mode?",
        choices=["y", "n", "unknown"],
        default="unknown"
    )

    if enable_thinking.lower() == "y":
        return True
    elif enable_thinking.lower() == "n":
        return False
    else:
        # For unknown models, default to enabled but warn the user
        console.print("[yellow]Enabling thinking mode by default. If you notice issues with model responses, you can disable it with /thinking-mode[/yellow]")
        return True

def chat_with_model(config, conversation_history=None, plugins=None):
    """ Main chat loop with model interaction and plugin support """
    if plugins is None:
        plugins = []

    # Add plugin commands to help
    plugin_commands = []
    for plugin in plugins:
        plugin_commands.extend(plugin.get_commands())

    if conversation_history is None:
        # Use user's thinking mode preference instead of model detection
        if config['thinking_mode']:
            # Make the thinking instruction more explicit and mandatory
            thinking_instruction = (
                f"{config['system_instructions']}\n\n"
                "CRITICAL INSTRUCTION: For EVERY response without exception, you MUST first explain your "
                "thinking process between <thinking> and </thinking> tags, even for simple greetings or short "
                "responses. This thinking section should explain your reasoning and approach. "
                "After the thinking section, provide your final response. Example format:\n"
                "<thinking>Here I analyze what to say, considering context and appropriate responses...</thinking>\n"
                "This is my actual response to the user."
            )
        else:
            # Use standard instructions without thinking tags
            thinking_instruction = config['system_instructions']

        conversation_history = [
            {"role": "system", "content": thinking_instruction}
        ]

        # Store thinking preference in conversation history for stream_response to use
        conversation_history.append({"role": "system", "name": "config", "content":
                                    f"thinking_mode: {config['thinking_mode']}"})

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    # Check if temperature is too high and warn the user
    if config['temperature'] > 1.0:
        console.print(Panel.fit(
            f"[yellow]Warning: High temperature setting ({config['temperature']}) may cause erratic responses.[/yellow]\n"
            f"Consider using a value between 0.0 and 1.0 for more coherent outputs.",
            title="⚠️ High Temperature Warning",
            border_style="yellow"
        ))

    console.print(Panel.fit(
        f"[bold blue]Or[/bold blue][bold green]Chat[/bold green] [dim]v{APP_VERSION}[/dim]\n"
        f"[cyan]Model:[/cyan] {config['model']}\n"
        f"[cyan]Temperature:[/cyan] {config['temperature']}\n"
        f"[cyan]Thinking mode:[/cyan] {'[green]✓ Enabled[/green]' if config['thinking_mode'] else '[yellow]✗ Disabled[/yellow]'}\n"
        f"[cyan]Session started:[/cyan] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Type your message or use commands: /help for available commands",
        title="🤖 Chat Session Active",
        border_style="green"
    ))

    # Add session tracking
    session_start_time = time.time()
    total_tokens_used = 0
    response_times = []
    message_count = 0

    # Create a session directory for saving files
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Auto-save conversation periodically
    last_autosave = time.time()
    autosave_interval = config['autosave_interval']

    # Check if we need to trim the conversation history
    conversation_history, trimmed_count = manage_context_window(conversation_history)
    if trimmed_count > 0:
        console.print(f"[yellow]Note: Removed {trimmed_count} earlier messages to stay within the context window.[/yellow]")

    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")

            # Handle special commands
            if user_input.startswith('/'):
                command = user_input.lower()

                if command == '/exit' or command == '/quit':
                    console.print("[yellow]Exiting chat...[/yellow]")
                    break

                if command == '/help':
                    console.print(Panel.fit(
                        "/exit - Exit the chat\n"
                        "/quit - Exit the chat\n"
                        "/new - Start a new conversation\n"
                        "/clear - Clear conversation history\n"
                        "/cls or /clear-screen - Clear terminal screen\n"  # Add this line
                        "/save - Save conversation to file\n"
                        "/settings - Adjust model settings\n"
                        "/tokens - Show token usage statistics\n"
                        "/model - Change the AI model\n"
                        "/temperature <0.0-2.0> - Adjust temperature\n"
                        "/system - View or change system instructions\n"
                        "/speed - Show response time statistics\n"
                        "/theme <theme> - Change the color theme\n"
                        "/about - Show information about OrChat\n"
                        "/update - Check for updates\n"
                        "/thinking - Show last AI thinking process\n"
                        "/thinking-mode - Toggle thinking mode on/off\n"
                        "/attach or /upload - Share a file with the AI",
                        title="Available Commands"
                    ))
                    continue

                elif command == '/clear':
                    conversation_history = [{"role": "system", "content": config['system_instructions']}]
                    console.print("[green]Conversation history cleared![/green]")
                    continue

                elif command == '/new':
                    # Check if there's any actual conversation to save
                    if len(conversation_history) > 1:
                        save_prompt = Prompt.ask(
                            "Would you like to save the current conversation before starting a new one?",
                            choices=["y", "n"],
                            default="n"
                        )

                        if save_prompt.lower() == "y":
                            # Auto-generate a filename with timestamp
                            filename = f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                            filepath = os.path.join(session_dir, filename)
                            save_conversation(conversation_history, filepath, "markdown")
                            console.print(f"[green]Conversation saved to {filepath}[/green]")

                    # Reset conversation
                    conversation_history = [{"role": "system", "content": config['system_instructions']}]

                    # Reset session tracking variables
                    total_tokens_used = 0
                    response_times = []
                    message_count = 0
                    last_autosave = time.time()

                    # Create a new session directory
                    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions", session_id)
                    os.makedirs(session_dir, exist_ok=True)

                    console.print(Panel.fit(
                        "[green]New conversation started![/green]\n"
                        "Previous conversation history has been cleared.",
                        title="🔄 New Conversation",
                        border_style="green"
                    ))
                    continue

                elif command == '/save':
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        filename = parts[1]
                    else:
                        filename = Prompt.ask("Enter filename to save conversation",
                                            default=f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

                    format_options = ["markdown", "json", "html"]
                    format_choice = Prompt.ask("Choose format", choices=format_options, default="markdown")

                    if not filename.endswith(f".{format_choice.split('.')[-1]}"):
                        if format_choice == "markdown":
                            filename += ".md"
                        elif format_choice == "json":
                            filename += ".json"
                        elif format_choice == "html":
                            filename += ".html"

                    filepath = os.path.join(session_dir, filename)
                    save_conversation(conversation_history, filepath, format_choice)
                    console.print(f"[green]Conversation saved to {filepath}[/green]")
                    continue

                elif command == '/settings':
                    console.print(Panel.fit(
                        f"Current Settings:\n"
                        f"Model: {config['model']}\n"
                        f"Temperature: {config['temperature']}\n"
                        f"System Instructions: {config['system_instructions'][:50]}...",
                        title="Settings"
                    ))
                    continue

                elif command == '/tokens':
                    console.print(f"[cyan]Total tokens used in this session: {total_tokens_used}[/cyan]")
                    continue

                elif command == '/speed':
                    if not response_times:
                        console.print("[yellow]No response time data available yet.[/yellow]")
                    else:
                        avg_time = sum(response_times) / len(response_times)
                        min_time = min(response_times)
                        max_time = max(response_times)
                        console.print(Panel.fit(
                            f"Response Time Statistics:\n"
                            f"Average: {format_time_delta(avg_time)}\n"
                            f"Fastest: {format_time_delta(min_time)}\n"
                            f"Slowest: {format_time_delta(max_time)}\n"
                            f"Total responses: {len(response_times)}",
                            title="Speed Statistics"
                        ))
                    continue

                elif command.startswith('/model'):
                    selected_model = select_model(config)
                    if selected_model:
                        config['model'] = selected_model
                        save_config(config)
                        console.print(f"[green]Model changed to {config['model']}[/green]")
                    else:
                        console.print("[yellow]Model selection cancelled[/yellow]")
                    continue

                elif command.startswith('/temperature'):
                    parts = command.split()
                    if len(parts) > 1:
                        try:
                            temp = float(parts[1])
                            if 0 <= temp <= 2:
                                if temp > 1.0:
                                    console.print("[yellow]Warning: High temperature values (>1.0) may cause erratic or nonsensical responses.[/yellow]")
                                    confirm = Prompt.ask("Are you sure you want to use this high temperature? (y/n)", default="n")
                                    if confirm.lower() != 'y':
                                        continue

                                config['temperature'] = temp
                                save_config(config)
                                console.print(f"[green]Temperature set to {temp}[/green]")
                            else:
                                console.print("[red]Temperature must be between 0 and 2[/red]")
                        except ValueError:
                            console.print("[red]Invalid temperature value[/red]")
                    else:
                        new_temp = Prompt.ask("Enter new temperature (0.0-2.0)", default=str(config['temperature']))
                        try:
                            temp = float(new_temp)
                            if 0 <= temp <= 2:
                                if temp > 1.0:
                                    console.print("[yellow]Warning: High temperature values (>1.0) may cause erratic or nonsensical responses.[/yellow]")
                                    confirm = Prompt.ask("Are you sure you want to use this high temperature? (y/n)", default="n")
                                    if confirm.lower() != 'y':
                                        continue

                                config['temperature'] = temp
                                save_config(config)
                                console.print(f"[green]Temperature set to {temp}[/green]")
                            else:
                                console.print("[red]Temperature must be between 0 and 2[/red]")
                        except ValueError:
                            console.print("[red]Invalid temperature value[/red]")
                    continue

                elif command.startswith('/system'):
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        config['system_instructions'] = parts[1]
                        conversation_history[0] = {"role": "system", "content": config['system_instructions']}
                        save_config(config)
                        console.print("[green]System instructions updated![/green]")
                    else:
                        console.print(Panel(config['system_instructions'], title="Current System Instructions"))
                        change = Prompt.ask("Update system instructions? (y/n)", default="n")
                        if change.lower() == 'y':
                            console.print("[bold]Enter new system instructions (guide the AI's behavior)[/bold]")
                            console.print("[dim]Press Enter twice to finish[/dim]")
                            lines = []
                            empty_line_count = 0
                            while True:
                                line = input()
                                if not line:
                                    empty_line_count += 1
                                    if empty_line_count >= 2:  # Exit after two consecutive empty lines
                                        break
                                else:
                                    empty_line_count = 0  # Reset counter if non-empty line
                                    lines.append(line)
                            system_instructions = "\n".join(lines)
                            config['system_instructions'] = system_instructions
                            conversation_history[0] = {"role": "system", "content": config['system_instructions']}
                            save_config(config)
                            console.print("[green]System instructions updated![/green]")
                    continue

                elif command.startswith('/attach') or command.startswith('/upload'):
                    # Extract file path from command
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        file_path = parts[1]
                    else:
                        console.print("[yellow]Please specify a file to attach.[/yellow]")
                        file_path = Prompt.ask("Enter the path to the file you want to attach")

                    # Check if file exists
                    if not os.path.exists(file_path):
                        console.print(f"[red]File not found: {file_path}[/red]")
                        continue

                    # Show attachment preview
                    file_name = os.path.basename(file_path)
                    file_ext = os.path.splitext(file_path)[1].lower()
                    file_size = os.path.getsize(file_path)
                    file_size_formatted = format_file_size(file_size)

                    console.print(Panel.fit(
                        f"File: [bold]{file_name}[/bold]\n"
                        f"Type: {file_ext[1:].upper() if file_ext else 'Unknown'}\n"
                        f"Size: {file_size_formatted}",
                        title="📎 Attachment Preview",
                        border_style="cyan"
                    ))

                    confirm = Prompt.ask("Attach this file? (y/n)", default="y")
                    if confirm.lower() != 'y':
                        console.print("[yellow]Attachment cancelled.[/yellow]")
                        continue

                    # Process the attachment
                    success, message = handle_attachment(file_path, conversation_history)
                    console.print(f"[{'green' if success else 'red'}]{message}[/{'green' if success else 'red'}]")

                    if success:
                        # Prompt for additional comment or context
                        add_comment = Prompt.ask("Add a comment about this attachment? (y/n)", default="n")
                        if add_comment.lower() == 'y':
                            comment = Prompt.ask("Enter your comment")
                            # Replace the last message with comment included
                            if conversation_history[-1]["role"] == "user":
                                if isinstance(conversation_history[-1]["content"], list):
                                    # For multimodal messages
                                    conversation_history[-1]["content"][0]["text"] += f"\n\n{comment}"
                                else:
                                    # For text messages
                                    conversation_history[-1]["content"] += f"\n\n{comment}"

                        console.print("[yellow]Attachment added to conversation. Send a message or press Enter to get AI response.[/yellow]")
                    continue

                elif command == '/about':
                    show_about()
                    continue

                elif command == '/update':
                    check_for_updates()
                    continue

                elif command == '/thinking':
                    if last_thinking_content:
                        console.print(Panel.fit(
                            last_thinking_content,
                            title="🧠 Last Thinking Process",
                            border_style="yellow"
                        ))
                    else:
                        console.print("[yellow]No thinking content available from the last response.[/yellow]")
                    continue

                elif command == '/thinking-mode':
                    # Toggle thinking mode
                    config['thinking_mode'] = not config['thinking_mode']
                    save_config(config)

                    # Update conversation history with new setting
                    # First, remove any existing thinking mode settings
                    conversation_history = [msg for msg in conversation_history
                                            if not (msg.get('name') == 'config' and 'thinking_mode' in msg.get('content', ''))]

                    # Add new setting
                    conversation_history.append({"role": "system", "name": "config",
                                                "content": f"thinking_mode: {config['thinking_mode']}"})

                    # Also update the system prompt for future messages
                    if len(conversation_history) > 0 and conversation_history[0]['role'] == 'system':
                        original_instructions = config['system_instructions']
                        if config['thinking_mode']:
                            thinking_instruction = (
                                f"{original_instructions}\n\n"
                                "CRITICAL INSTRUCTION: For EVERY response without exception, you MUST first explain your "
                                "thinking process between <thinking> and </thinking> tags, even for simple greetings or short "
                                "responses. This thinking section should explain your reasoning and approach. "
                                "After the thinking section, provide your final response. Example format:\n"
                                "<thinking>Here I analyze what to say, considering context and appropriate responses...</thinking>\n"
                                "This is my actual response to the user."
                            )
                            conversation_history[0]['content'] = thinking_instruction
                        else:
                            # Revert to original instructions without thinking tags
                            conversation_history[0]['content'] = original_instructions

                    console.print(f"[green]Thinking mode is now {'enabled' if config['thinking_mode'] else 'disabled'}[/green]")
                    continue

                elif command in ('/cls', '/clear-screen'):

                    # Clear the terminal
                    clear_terminal()

                    # After clearing, redisplay the session header for context
                    console.print(Panel.fit(
                        f"[bold blue]Or[/bold blue][bold green]Chat[/bold green] [dim]v{APP_VERSION}[/dim]\n"
                        f"[cyan]Model:[/cyan] {config['model']}\n"
                        f"[cyan]Temperature:[/cyan] {config['temperature']}\n"
                        f"[cyan]Thinking mode:[/cyan] {'[green]✓ Enabled[/green]' if config['thinking_mode'] else '[yellow]✗ Disabled[/yellow]'}\n"
                        f"[cyan]Session started:[/cyan] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Type your message or use commands: /help for available commands",
                        title="🤖 Chat Session Active",
                        border_style="green"
                    ))
                    console.print("[green]Terminal screen cleared. Chat session continues.[/green]")
                    continue

                else:
                    console.print("[yellow]Unknown command. Type /help for available commands.[/yellow]")
                    continue

            # Process plugin commands
            command_handled = False
            command_parts = user_input[1:].split(' ', 1)
            command = command_parts[0]
            args = command_parts[1] if len(command_parts) > 1 else ""

            for plugin in plugins:
                success, message = plugin.on_command(command, args)
                if success:
                    console.print(message)
                    command_handled = True
                    break

            if command_handled:
                continue

            # Process message through plugins
            for plugin in plugins:
                user_input = plugin.on_message(user_input, "user")

            # Count tokens in user input
            input_tokens = count_tokens(user_input)

            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": user_input})

            # Check if we need to trim the conversation history
            conversation_history, trimmed_count = manage_context_window(conversation_history)
            if trimmed_count > 0:
                console.print(f"[yellow]Note: Removed {trimmed_count} earlier messages to stay within the context window.[/yellow]")

            # Update the API call to use streaming
            data = {
                "model": config['model'],
                "messages": conversation_history,
                "temperature": config['temperature'],
                "stream": True,
            }

            # Start timing the response
            start_time = time.time()
            timer_display = console.status("[bold cyan]⏱️ Waiting for response...[/bold cyan]")
            timer_display.start()

            try:
                # Make streaming request
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    stream=True,
                    timeout=60  # Add a timeout
                )

                if response.status_code == 200:
                    # Pass config['thinking_mode'] to stream_response
                    message_content, response_time = stream_response(response, start_time, config['thinking_mode'])

                    # Only add to history if we got actual content
                    if message_content:
                        response_times.append(response_time)

                        # Add assistant response to conversation history
                        conversation_history.append({"role": "assistant", "content": message_content})

                        # Count tokens and update total
                        response_tokens = count_tokens(message_content)
                        total_tokens_used += input_tokens + response_tokens

                        # Display speed and token information
                        formatted_time = format_time_delta(response_time)
                        console.print(f"[dim]⏱️ Response time: {formatted_time}[/dim]")
                        console.print(f"[dim]Tokens: {input_tokens} (input) + {response_tokens} (response) = {input_tokens + response_tokens} (total)[/dim]")
                    else:
                        # If we didn't get content but status was 200, something went wrong with streaming
                        console.print("[red]Error: Received empty response from API[/red]")
                        # Remove the user's last message since we didn't get a response
                        if conversation_history and conversation_history[-1]["role"] == "user":
                            conversation_history.pop()
                else:
                    # Try to get error details from response
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', str(response.text))
                        console.print(f"[red]API Error ({response.status_code}): {error_message}[/red]")
                    except Exception:
                        console.print(f"[red]API Error: Status code {response.status_code}[/red]")
                        console.print(f"[red]{response.text}[/red]")

                    # Remove the user's last message since we didn't get a response
                    if conversation_history and conversation_history[-1]["role"] == "user":
                        conversation_history.pop()
            except requests.exceptions.RequestException as e:
                console.print(f"[red]Network error: {str(e)}[/red]")
                # Remove the user's last message since we didn't get a response
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                # Remove the user's last message since we didn't get a response
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()
            finally:
                timer_display.stop()

        except KeyboardInterrupt:
            console.print("\n[yellow]Keyboard interrupt detected. Type /exit to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

def create_chat_ui():
    """Creates a modern, attractive CLI interface using rich components"""
    console.print(Panel.fit(
        f"[bold blue]Or[/bold blue][bold green]Chat[/bold green] [dim]v{APP_VERSION}[/dim]\n"
        "[dim]A powerful CLI for AI models via OpenRouter[/dim]",
        title="🚀 Welcome",
        border_style="green",
        padding=(1, 2)
    ))

    # Display a starting tip
    console.print(Panel(
        "Type [bold green]/help[/bold green] for commands\n"
        "[bold cyan]/model[/bold cyan] to change AI models\n"
        "[bold yellow]/theme[/bold yellow] to customize appearance",
        title="Quick Tips",
        border_style="blue",
        width=40
    ))

def main():
    parser = argparse.ArgumentParser(description="OrChat - AI chat powered by OpenRouter")
    parser.add_argument("--setup", action="store_true", help="Run the setup wizard")
    parser.add_argument("--model", type=str, help="Specify model to use")
    parser.add_argument("--task", type=str, choices=["creative", "coding", "analysis", "chat"],
                        help="Optimize for specific task type")
    parser.add_argument("--image", type=str, help="Path to image file to analyze")
    args = parser.parse_args()

    # Check if config exists
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

    if args.setup or (not os.path.exists(config_file) and not os.path.exists(env_file)):
        config = setup_wizard()
    else:
        config = load_config()

    # Show welcome UI
    create_chat_ui()

    # Check if API key is set
    if not config['api_key'] or config['api_key'] == "<YOUR_OPENROUTER_API_KEY>":
        console.print("[red]API key not found or not set correctly.[/red]")
        setup_choice = Prompt.ask("Would you like to run the setup wizard? (y/n)", default="y")
        if setup_choice.lower() == 'y':
            config = setup_wizard()
        else:
            console.print("[red]Cannot continue without a valid API key. Exiting.[/red]")
            sys.exit(1)

    # Handle task-specific model recommendation
    if args.task:
        recommended_models = get_model_recommendations(args.task)
        if recommended_models:
            console.print(Panel.fit(
                f"[bold green]Recommended models for {args.task} tasks:[/bold green]\n" +
                "\n".join([f"- {model['id']}" for model in recommended_models[:5]]),
                title="🎯 Task Optimization"
            ))

            use_recommended = Prompt.ask(
                "Would you like to use one of these recommended models?",
                choices=["y", "n"],
                default="y"
            )

            if use_recommended.lower() == 'y':
                # Let user select from recommended models
                for i, model in enumerate(recommended_models[:5], 1):
                    console.print(f"[bold]{i}.[/bold] {model['id']}")

                choice = Prompt.ask("Select model number", default="1")
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(recommended_models[:5]):
                        config['model'] = recommended_models[index]['id']
                        save_config(config)
                except ValueError:
                    pass

    # Check if model is set or specified via command line
    if args.model:
        config['model'] = args.model
        save_config(config)
    elif not config['model']:
        console.print("[yellow]No model selected. Please choose a model.[/yellow]")
        selected_model = select_model(config)
        if selected_model:
            config['model'] = selected_model
            save_config(config)
        else:
            console.print("[red]Cannot continue without a valid model. Exiting.[/red]")
            sys.exit(1)

    # Check if system instructions are set - make sure we don't prompt again after setup
    if not config['system_instructions']:
        # Only prompt for system instructions if they weren't already set during setup
        # Set a default value without prompting
        config['system_instructions'] = "You are a helpful AI assistant."
        console.print("[yellow]No system instructions set. Using default instructions.[/yellow]")
        save_config(config)

    # Handle image analysis if provided
    conversation_history = None
    if args.image:
        conversation_history = [
            {"role": "system", "content": config['system_instructions']}
        ]
        success, message = multimodal_support(args.image, conversation_history)
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[red]{message}[/red]")

    # Start chat with optimized streaming settings
    streaming_config = optimize_streaming()
    plugins = load_plugins()
    chat_with_model(config, conversation_history, plugins)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application...")
    except Exception as e:
        console.print(f"[red]Critical error: {str(e)}[/red]")
        sys.exit(1)

# Add these conversation management features
def export_conversation(conversation_history, fmt="markdown", include_system=False):
    """Export conversation in multiple formats with advanced options"""
    formats = {
        "markdown": export_markdown,
        "json": export_json,
        "html": export_html,
        "pdf": export_pdf,
        "txt": export_txt
    }

    if fmt in formats:
        return formats[fmt](conversation_history, include_system)
    return export_markdown(conversation_history, include_system)

def chat_context_manager(conversation_history, max_tokens=8000):
    """Advanced context window management with summarization"""
    # If approaching token limit, create a summary of older messages
    if sum(count_tokens(msg["content"]) for msg in conversation_history) > (max_tokens * 0.8):
        # Extract older messages for summarization
        older_messages = conversation_history[1:len(conversation_history)//2]

        # Create a summary prompt
        summary_prompt = "Summarize the following conversation:\n\n"
        for msg in older_messages:
            summary_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n\n"

        # Get summary from model
        summary = get_summary_from_model(summary_prompt)

        # Replace older messages with summary
        conversation_history = [
            conversation_history[0],  # Keep system prompt
            {"role": "system", "content": f"Summary of previous conversation: {summary}"},
            *conversation_history[len(conversation_history)//2:]  # Keep newer messages
        ]

    return conversation_history

# Enhanced model management
def get_model_recommendations(task_type=None, budget=None):
    """Recommends models based on task type and budget constraints"""
    all_models = get_available_models()

    if not task_type:
        return all_models

    task_categories = {
        "creative": ["claude-3", "gpt-4", "llama", "gemini"],
        "coding": ["claude-3-opus", "gpt-4", "deepseek-coder"],
        "analysis": ["claude-3-opus", "gpt-4", "mistral"],
        "chat": ["claude-3-haiku", "gpt-3.5", "gemini-pro"]
    }

    recommended = []
    for model in all_models:
        # Filter by task suitability
        if any(model_family in model['id'].lower() for model_family in task_categories.get(task_type, [])):
            # Filter by budget if specified
            if budget == "free" and ":free" in model['id']:
                recommended.append(model)
            elif budget is None or budget != "free":
                recommended.append(model)

    return recommended or all_models

# Add these powerful features
def multimodal_support(file_path, conversation_history):
    """Handle images and other non-text content"""
    file_ext = os.path.splitext(file_path)[1].lower()

    # Handle different file types
    if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        # Encode image to base64
        with open(file_path, 'rb', encoding="utf-8") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')

        # Add to messages with proper format for multimodal models
        conversation_history.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "I'm sharing this image with you:"},
                {"type": "image_url", "image_url": {"url": f"data:image/{file_ext[1:]};base64,{base64_image}"}}
            ]
        })
        return True, f"Image '{os.path.basename(file_path)}' attached successfully."

    return process_file_upload(file_path, conversation_history)

def tool_integration(conversation_history):
    """Add function calling capabilities for weather, search, etc."""
    # Define available tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    return tools

def conversation_search(conversation_history, query):
    """Search through conversation history"""
    results = []
    for i, msg in enumerate(conversation_history):
        if query.lower() in msg["content"].lower():
            results.append((i, msg))

    return results

def auto_completion(user_input, conversation_history):
    """Provide smart tab completion based on conversation context"""
    # Detect command completion
    if user_input.startswith('/'):
        commands = ['/help', '/model', '/save', '/theme', '/exit', '/quit', '/clear',
                   '/tokens', '/system', '/search', '/execute', '/upload']
        matching = [cmd for cmd in commands if cmd.startswith(user_input)]
        return matching

    # Context-aware suggestions based on conversation
    recent_keywords = extract_keywords(conversation_history[-5:])
    return [kw for kw in recent_keywords if kw.startswith(user_input)]

def session_persistence(session_dir, conversation_history):
    """Automatically save sessions for crash recovery"""
    # Create backup file path
    backup_path = os.path.join(session_dir, "backup.json")

    # Save the current state
    with open(backup_path, 'w', encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "conversation": conversation_history
        }, f)

    # Return recovery function
    def recover_session():
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r',  encoding="utf-8") as f:
                    data = json.load(f)
                return data["conversation"]
            except:
                return None
        return None

    return recover_session

def interactive_help():
    """Provide interactive help with examples"""
    help_sections = {
        "basics": [
            ("Starting a conversation", "Simply type your message and press Enter"),
            ("Changing models", "Use /model to select from available AI models"),
            ("Saving your chat", "Use /save to export your conversation")
        ],
        "advanced": [
            ("Code execution", "The assistant can generate and you can run code with /execute"),
            ("File uploads", "Share files with /upload [filepath]"),
            ("Multimodal", "Share images and get AI analysis")
        ],
        "tips": [
            ("For creative tasks", "Try models like Claude-3 Opus or GPT-4"),
            ("For coding help", "DeepSeek Coder or Claude-3 Opus excel at programming"),
            ("For faster responses", "Haiku models are optimized for speed")
        ]
    }

    # Display interactive menu
    console.print("[bold green]OrChat Help[/bold green]\n")

    section = Prompt.ask(
        "Choose a help section",
        choices=["basics", "advanced", "tips", "all"],
        default="basics"
    )

    if section == "all":
        for sec_name, items in help_sections.items():
            console.print(f"\n[bold cyan]{sec_name.capitalize()}[/bold cyan]")
            for title, desc in items:
                console.print(f"[bold]{title}:[/bold] {desc}")
    else:
        console.print(f"\n[bold cyan]{section.capitalize()}[/bold cyan]")
        for title, desc in help_sections[section]:
            console.print(f"[bold]{title}:[/bold] {desc}")

def extract_keywords(messages, max_keywords=10):
    """Extract important keywords from recent conversation messages"""
    # Combine all message content
    all_text = " ".join([msg["content"] for msg in messages if isinstance(msg["content"], str)])

    # Simple keyword extraction - remove common words and punctuation
    common_words = {"the", "and", "a", "to", "of", "is", "in", "that", "it", "with",
                   "for", "as", "on", "at", "by", "an", "be", "this", "are", "or", "was"}

    # Clean and tokenize text
    words = re.findall(r'\b\w+\b', all_text.lower())

    # Count word frequencies, excluding common words
    word_counts = Counter([w for w in words if w not in common_words and len(w) > 2])

    # Return most common keywords
    return [word for word, count in word_counts.most_common(max_keywords)]

def get_summary_from_model(summary_prompt):
    """Get a summary of conversation from the model"""
    # Use the current model to generate a summary
    config = load_config()

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    data = {
        "model": config['model'],
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely."},
            {"role": "user", "content": summary_prompt}
        ],
        "temperature": 0.3,  # Lower temperature for more factual summary
        "max_tokens": 300    # Limit summary length
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        return "Previous conversation summary unavailable."
    except Exception:
        return "Previous conversation summary unavailable."

def export_markdown(conversation_history, include_system=False):
    """Export conversation to markdown format"""
    output = "# OrChat Conversation\n\n"
    output += f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for msg in conversation_history:
        if msg['role'] == 'system' and not include_system:
            continue

        output += f"## {msg['role'].capitalize()}\n\n{msg['content']}\n\n"

    return output

def export_json(conversation_history, include_system=True):
    """Export conversation to JSON format"""
    if not include_system:
        # Filter out system messages
        filtered_history = [msg for msg in conversation_history if msg['role'] != 'system']
        return json.dumps(filtered_history, indent=2)
    return json.dumps(conversation_history, indent=2)

def export_html(conversation_history, include_system=False):
    """Export conversation to HTML format"""
    html = ("""<!DOCTYPE html>
<html>
<head>
    <title>OrChat Conversation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .system { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
        .user { background-color: #e1f5fe; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .assistant { background-color: #f1f8e9; padding: 10px; border-radius: 5px; margin: 10px 0; }
        h1, h2 { color: #333; }
    </style>
</head>
<body>
    <h1>OrChat Conversation</h1>
    <p>Date: """ + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "</p>\n")

    for msg in conversation_history:
        if msg['role'] == 'system' and not include_system:
            continue

        content_html = msg['content'].replace('\n', '<br>')
        html += f"""
    <div class="{msg['role']}">
        <h2>{msg['role'].capitalize()}</h2>
        <p>{content_html}</p>
    </div>
"""

    html += """
</body>
</html>
"""
    return html

def export_txt(conversation_history, include_system=False):
    """Export conversation to plain text format"""
    output = "OrChat Conversation\n"
    output += f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for msg in conversation_history:
        if msg['role'] == 'system' and not include_system:
            continue

        output += f"{msg['role'].upper()}:\n{msg['content']}\n\n"

    return output

def export_pdf(conversation_history, include_system=False):
    """Export conversation to PDF format"""
    try:
        # Check if reportlab is installed
        if importlib.util.find_spec("reportlab") is None:
            console.print("[yellow]ReportLab package not found. Installing...[/yellow]")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])

        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name

        # Create the PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()

        # Add content to the PDF
        content = []
        content.append(Paragraph("OrChat Conversation", styles['Title']))
        content.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        content.append(Spacer(1, 12))

        for msg in conversation_history:
            if msg['role'] == 'system' and not include_system:
                continue

            content.append(Paragraph(f"{msg['role'].upper()}:", styles['Heading2']))
            # Split content by lines to maintain formatting
            for line in msg['content'].split('\n'):
                if line.strip():
                    content.append(Paragraph(line, styles['Normal']))
                else:
                    content.append(Spacer(1, 6))
            content.append(Spacer(1, 12))

        # Build the PDF
        doc.build(content)
        return pdf_path
    except Exception as e:
        console.print(f"[red]Error creating PDF: {str(e)}[/red]")
        # Fallback to markdown if PDF creation fails
        return export_markdown(conversation_history, include_system)

# 1. Add a new function to clear the terminal screen
def clear_terminal():
    """Clear the terminal screen"""
    # Use a cross-platform approach for clearing the terminal
    print("\x1b[2J\x1b[H")