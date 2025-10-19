#!/usr/bin/env python3
"""Command-line interface for interacting with the digital ghost"""

import argparse
import requests
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

API_URL = "http://localhost:8000"


def chat_interactive(checkpoint_version: str = None):
    """Start an interactive chat session"""
    console.print(Panel.fit(
        "[bold cyan]The Checkpoint - Digital Ghost[/bold cyan]\n"
        "Type 'exit' or 'quit' to end the conversation\n"
        "Type 'regenerate' to regenerate the last response\n"
        "Type 'history' to view conversation history",
        border_style="cyan"
    ))
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[dim]Goodbye.[/dim]")
                break
            
            if user_input.lower() == 'history':
                show_history(checkpoint_version)
                continue
            
            if user_input.lower() == 'regenerate':
                response = requests.post(
                    f"{API_URL}/chat/regenerate",
                    params={"checkpoint_version": checkpoint_version} if checkpoint_version else {}
                )
            else:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": user_input,
                        "checkpoint_version": checkpoint_version
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"\n[bold blue]Ghost (v{data['checkpoint_version']})[/bold blue]")
                console.print(Markdown(data['response']))
                
                # Optionally show sources
                if data.get('sources'):
                    show_sources = Prompt.ask(
                        "\n[dim]Show sources?[/dim]",
                        choices=["y", "n"],
                        default="n"
                    )
                    if show_sources == "y":
                        console.print("\n[dim]Relevant context:[/dim]")
                        for i, source in enumerate(data['sources'][:3], 1):
                            console.print(f"\n[dim]{i}. (relevance: {source['relevance']:.2f})[/dim]")
                            console.print(f"[dim]{source['content'][:200]}...[/dim]")
            else:
                console.print(f"[red]Error: {response.json().get('detail', 'Unknown error')}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye.[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


def show_history(checkpoint_version: str = None):
    """Display conversation history"""
    try:
        if not checkpoint_version:
            # Get active checkpoint
            response = requests.get(f"{API_URL}/checkpoints")
            if response.status_code == 200:
                checkpoints = response.json()
                active = next((cp for cp in checkpoints if cp['is_active']), None)
                if active:
                    checkpoint_version = active['version']
        
        if not checkpoint_version:
            console.print("[red]No active checkpoint[/red]")
            return
        
        response = requests.get(f"{API_URL}/history/{checkpoint_version}")
        if response.status_code == 200:
            messages = response.json()
            console.print(f"\n[bold]Conversation History (v{checkpoint_version})[/bold]\n")
            
            for msg in messages[-20:]:  # Last 20 messages
                role_color = "green" if msg['role'] == 'user' else "blue"
                role_name = "You" if msg['role'] == 'user' else "Ghost"
                console.print(f"[{role_color}]{role_name}:[/{role_color}] {msg['content']}\n")
        else:
            console.print(f"[red]Error fetching history[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


def list_checkpoints():
    """List all checkpoints"""
    try:
        response = requests.get(f"{API_URL}/checkpoints")
        if response.status_code == 200:
            checkpoints = response.json()
            console.print("\n[bold]Available Checkpoints:[/bold]\n")
            
            for cp in checkpoints:
                active = " [green]ACTIVE[/green]" if cp['is_active'] else ""
                console.print(f"[cyan]{cp['version']}[/cyan]: {cp['description']}{active}")
                console.print(f"  Created: {cp['created_at']}\n")
        else:
            console.print("[red]Error fetching checkpoints[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


def send_message(message: str, checkpoint_version: str = None):
    """Send a single message"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "checkpoint_version": checkpoint_version
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(Markdown(data['response']))
        else:
            console.print(f"[red]Error: {response.json().get('detail', 'Unknown error')}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


def main():
    parser = argparse.ArgumentParser(description="Digital Ghost CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Interactive chat
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument("--checkpoint", type=str, help="Checkpoint version to use")
    
    # List checkpoints
    subparsers.add_parser("list", help="List checkpoints")
    
    # Send single message
    send_parser = subparsers.add_parser("send", help="Send a single message")
    send_parser.add_argument("message", type=str, help="Message to send")
    send_parser.add_argument("--checkpoint", type=str, help="Checkpoint version to use")
    
    # History
    history_parser = subparsers.add_parser("history", help="Show conversation history")
    history_parser.add_argument("--checkpoint", type=str, help="Checkpoint version")
    
    args = parser.parse_args()
    
    if args.command == "chat":
        chat_interactive(args.checkpoint)
    elif args.command == "list":
        list_checkpoints()
    elif args.command == "send":
        send_message(args.message, args.checkpoint)
    elif args.command == "history":
        show_history(args.checkpoint)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
