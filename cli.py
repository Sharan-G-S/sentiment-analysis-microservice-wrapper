#!/usr/bin/env python3
"""
CLI tool for testing the sentiment analysis API
"""
import argparse
import sys
import json
import requests
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint


console = Console()


class SentimentClient:
    """Client for interacting with the sentiment API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> dict:
        """Get API metrics"""
        response = self.session.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()
    
    def predict(
        self, 
        text: str, 
        return_probabilities: bool = False,
        request_id: Optional[str] = None
    ) -> dict:
        """Predict sentiment for text"""
        payload = {
            "text": text,
            "return_probabilities": return_probabilities
        }
        if request_id:
            payload["request_id"] = request_id
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(
        self, 
        texts: list, 
        return_probabilities: bool = False
    ) -> dict:
        """Predict sentiment for multiple texts"""
        payload = {
            "texts": texts,
            "return_probabilities": return_probabilities
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/predict/batch",
            json=payload
        )
        response.raise_for_status()
        return response.json()


def cmd_health(args):
    """Health check command"""
    client = SentimentClient(args.url)
    
    try:
        result = client.health_check()
        
        status_color = "green" if result['status'] == 'healthy' else "red"
        
        console.print(Panel(
            f"[bold {status_color}]{result['status'].upper()}[/bold {status_color}]\n"
            f"Model Loaded: {result['model_loaded']}\n"
            f"Version: {result['version']}\n"
            f"Timestamp: {result['timestamp']}",
            title="Health Check",
            border_style=status_color
        ))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def cmd_metrics(args):
    """Metrics command"""
    client = SentimentClient(args.url)
    
    try:
        result = client.get_metrics()
        
        table = Table(title="API Metrics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(result['total_requests']))
        table.add_row("Successful", str(result['successful_requests']))
        table.add_row("Failed", str(result['failed_requests']))
        table.add_row("Avg Latency (ms)", f"{result['average_latency_ms']:.2f}")
        table.add_row("Uptime (s)", f"{result['uptime_seconds']:.2f}")
        
        console.print(table)
        
        # Model info
        console.print("\n[bold]Model Information:[/bold]")
        for key, value in result['model_info'].items():
            console.print(f"  {key}: {value}")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def cmd_predict(args):
    """Predict command"""
    client = SentimentClient(args.url)
    
    try:
        # Read input
        if args.file:
            with open(args.file, 'r') as f:
                text = f.read().strip()
        else:
            text = args.text
        
        # Make prediction
        result = client.predict(
            text=text,
            return_probabilities=args.probabilities,
            request_id=args.request_id
        )
        
        # Display result
        sentiment_color = "green" if result['sentiment'] == 'positive' else "red"
        
        output = (
            f"[bold {sentiment_color}]Sentiment: {result['sentiment'].upper()}[/bold {sentiment_color}]\n"
            f"Confidence: {result['confidence']:.2%}\n"
            f"Latency: {result['latency_ms']:.2f}ms"
        )
        
        if result.get('probabilities'):
            output += "\n\nProbabilities:"
            for label, prob in result['probabilities'].items():
                output += f"\n  {label}: {prob:.2%}"
        
        console.print(Panel(output, title="Prediction Result", border_style=sentiment_color))
        
        # JSON output if requested
        if args.json:
            console.print("\n[dim]JSON Output:[/dim]")
            console.print_json(data=result)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def cmd_batch(args):
    """Batch prediction command"""
    client = SentimentClient(args.url)
    
    try:
        # Read texts from file
        with open(args.file, 'r') as f:
            texts = [line.strip() for line in f if line.strip()]
        
        console.print(f"Processing {len(texts)} texts...")
        
        # Make batch prediction
        result = client.predict_batch(
            texts=texts,
            return_probabilities=args.probabilities
        )
        
        # Display results
        table = Table(title=f"Batch Prediction Results ({len(result['predictions'])} items)")
        table.add_column("Text", style="cyan", max_width=50)
        table.add_column("Sentiment", style="bold")
        table.add_column("Confidence", style="green")
        table.add_column("Latency (ms)", style="yellow")
        
        for idx, pred in enumerate(result['predictions']):
            text_preview = texts[idx][:47] + "..." if len(texts[idx]) > 50 else texts[idx]
            sentiment_style = "green" if pred['sentiment'] == 'positive' else "red"
            
            table.add_row(
                text_preview,
                f"[{sentiment_style}]{pred['sentiment']}[/{sentiment_style}]",
                f"{pred['confidence']:.2%}",
                f"{pred['latency_ms']:.2f}"
            )
        
        console.print(table)
        console.print(f"\nTotal latency: {result['total_latency_ms']:.2f}ms")
        
        # JSON output if requested
        if args.json:
            console.print("\n[dim]JSON Output:[/dim]")
            console.print_json(data=result)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def cmd_interactive(args):
    """Interactive mode"""
    client = SentimentClient(args.url)
    
    console.print("[bold green]Interactive Sentiment Analysis[/bold green]")
    console.print("Type your text and press Enter to analyze. Type 'quit' to exit.\n")
    
    while True:
        try:
            text = console.input("[bold cyan]Text:[/bold cyan] ")
            
            if text.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if not text.strip():
                continue
            
            result = client.predict(text=text, return_probabilities=True)
            
            sentiment_color = "green" if result['sentiment'] == 'positive' else "red"
            console.print(
                f"  [{sentiment_color}]{result['sentiment'].upper()}[/{sentiment_color}] "
                f"(confidence: {result['confidence']:.2%}, "
                f"latency: {result['latency_ms']:.2f}ms)\n"
            )
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]\n")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for Sentiment Analysis API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='API base URL (default: http://localhost:8000)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Health command
    subparsers.add_parser('health', help='Check API health')
    
    # Metrics command
    subparsers.add_parser('metrics', help='Get API metrics')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Predict sentiment')
    predict_parser.add_argument('text', nargs='?', help='Text to analyze')
    predict_parser.add_argument('-f', '--file', help='Read text from file')
    predict_parser.add_argument('-p', '--probabilities', action='store_true', help='Return probabilities')
    predict_parser.add_argument('-r', '--request-id', help='Request ID')
    predict_parser.add_argument('-j', '--json', action='store_true', help='Output JSON')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch prediction from file')
    batch_parser.add_argument('file', help='File with one text per line')
    batch_parser.add_argument('-p', '--probabilities', action='store_true', help='Return probabilities')
    batch_parser.add_argument('-j', '--json', action='store_true', help='Output JSON')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to command handlers
    commands = {
        'health': cmd_health,
        'metrics': cmd_metrics,
        'predict': cmd_predict,
        'batch': cmd_batch,
        'interactive': cmd_interactive
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
