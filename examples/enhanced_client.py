#!/usr/bin/env python3
"""
Enhanced Sentiment Analysis Client
Demonstrates Groq/Gemini integration features
"""

import requests
import json
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

BASE_URL = "http://localhost:8001"


class EnhancedSentimentClient:
    """Client for enhanced sentiment analysis with LLM features"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def analyze_with_insights(
        self,
        text: str,
        provider: Optional[str] = None
    ) -> Dict:
        """
        Analyze text with enhanced LLM insights
        
        Args:
            text: Text to analyze
            provider: LLM provider ('groq', 'gemini', or None for auto)
        
        Returns:
            Full analysis result with enhanced insights
        """
        payload = {
            "text": text,
            "enhanced": True,
            "return_probabilities": True
        }
        
        if provider:
            payload["llm_provider"] = provider
        
        response = requests.post(
            f"{self.base_url}/api/v1/predict",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def batch_analyze_with_trends(
        self,
        texts: List[str],
        provider: Optional[str] = None
    ) -> Dict:
        """
        Analyze multiple texts and get trend insights
        
        Args:
            texts: List of texts to analyze
            provider: LLM provider
        
        Returns:
            Batch results with insights
        """
        payload = {
            "texts": texts,
            "enhanced": True,
            "return_probabilities": True
        }
        
        if provider:
            payload["llm_provider"] = provider
        
        response = requests.post(
            f"{self.base_url}/api/v1/predict/batch",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def compare_providers(self, text: str) -> Dict:
        """
        Compare results from different providers
        
        Args:
            text: Text to analyze
        
        Returns:
            Results from auto, groq, and gemini
        """
        results = {}
        
        for provider in [None, "groq", "gemini"]:
            try:
                result = self.analyze_with_insights(text, provider)
                provider_name = provider or "auto"
                results[provider_name] = {
                    "sentiment": result["sentiment"],
                    "confidence": result["confidence"],
                    "latency_ms": result["latency_ms"],
                    "explanation": result.get("enhanced_analysis", {}).get("explanation", "N/A"),
                    "key_phrases": result.get("enhanced_analysis", {}).get("key_phrases", [])
                }
            except Exception as e:
                results[provider_name] = {"error": str(e)}
        
        return results


def demo_single_analysis():
    """Demo: Single text analysis with enhanced insights"""
    console.print("\n[bold cyan]Demo 1: Enhanced Single Text Analysis[/bold cyan]\n")
    
    client = EnhancedSentimentClient()
    
    text = "This product exceeded all my expectations! The quality is outstanding and customer service was incredibly helpful. Highly recommend!"
    
    console.print(f"[yellow]Analyzing:[/yellow] {text}\n")
    
    result = client.analyze_with_insights(text)
    
    # Display results
    console.print(f"[green]Sentiment:[/green] {result['sentiment'].upper()}")
    console.print(f"[green]Confidence:[/green] {result['confidence']:.2%}")
    console.print(f"[green]Latency:[/green] {result['latency_ms']:.2f}ms\n")
    
    # Enhanced analysis
    enhanced = result.get("enhanced_analysis", {})
    
    console.print(Panel(
        enhanced.get("explanation", "No explanation available"),
        title="[bold]Detailed Explanation[/bold]",
        border_style="blue"
    ))
    
    if enhanced.get("key_phrases"):
        console.print("\n[yellow]Key Phrases:[/yellow]")
        for phrase in enhanced["key_phrases"]:
            console.print(f"  • {phrase}")
    
    if enhanced.get("reasoning"):
        console.print(f"\n[yellow]Reasoning:[/yellow]\n{enhanced['reasoning']}")


def demo_negative_feedback():
    """Demo: Negative feedback with actionable suggestions"""
    console.print("\n[bold cyan]Demo 2: Negative Feedback Analysis[/bold cyan]\n")
    
    client = EnhancedSentimentClient()
    
    text = "Terrible experience! The product arrived damaged, customer service was unresponsive, and getting a refund was a nightmare. Would not recommend to anyone."
    
    console.print(f"[yellow]Analyzing Complaint:[/yellow] {text}\n")
    
    result = client.analyze_with_insights(text)
    
    console.print(f"[red]Sentiment:[/red] {result['sentiment'].upper()}")
    console.print(f"[red]Confidence:[/red] {result['confidence']:.2%}\n")
    
    enhanced = result.get("enhanced_analysis", {})
    
    # Show key issues
    if enhanced.get("key_phrases"):
        console.print("[red]Key Issues Detected:[/red]")
        for phrase in enhanced["key_phrases"]:
            console.print(f"  🔴 {phrase}")
    
    # Show suggestions
    if enhanced.get("suggestions"):
        console.print("\n[green]Recommended Actions:[/green]")
        for i, suggestion in enumerate(enhanced["suggestions"], 1):
            console.print(f"  {i}. {suggestion}")


def demo_batch_insights():
    """Demo: Batch analysis with trend insights"""
    console.print("\n[bold cyan]Demo 3: Batch Analysis with Trends[/bold cyan]\n")
    
    client = EnhancedSentimentClient()
    
    reviews = [
        "Absolutely love this product! Best purchase I've made this year.",
        "Disappointed with the quality. Not worth the price.",
        "Great customer service and fast shipping. Very satisfied!",
        "Product broke after one week. Poor quality control.",
        "Exceeded my expectations! Highly recommend to everyone.",
        "Terrible experience. Would not buy again.",
        "Good value for money. Happy with my purchase.",
        "The worst product I've ever bought. Complete waste.",
        "Amazing quality and excellent customer support!",
        "Not as described. Very disappointed with this purchase."
    ]
    
    console.print(f"[yellow]Analyzing {len(reviews)} customer reviews...[/yellow]\n")
    
    result = client.batch_analyze_with_trends(reviews)
    
    # Show individual predictions
    table = Table(title="Individual Predictions")
    table.add_column("Review", style="cyan", no_wrap=False, width=50)
    table.add_column("Sentiment", justify="center")
    table.add_column("Confidence", justify="right")
    
    for pred in result["predictions"][:5]:  # Show first 5
        sentiment_color = "green" if pred["sentiment"] == "positive" else "red"
        table.add_row(
            result["predictions"][0]["request_id"],  # Would show text in real impl
            f"[{sentiment_color}]{pred['sentiment'].upper()}[/{sentiment_color}]",
            f"{pred['confidence']:.2%}"
        )
    
    console.print(table)
    console.print(f"\n[dim]...and {len(reviews) - 5} more reviews[/dim]\n")
    
    # Show insights
    insights = result.get("batch_insights", {})
    
    if insights:
        trends = insights.get("trends", {})
        
        console.print(Panel(
            insights.get("summary", "No summary available"),
            title="[bold]Overall Summary[/bold]",
            border_style="blue"
        ))
        
        console.print(f"\n[yellow]Sentiment Distribution:[/yellow]")
        console.print(f"  🟢 Positive: {trends.get('positive', 0):.1f}%")
        console.print(f"  🔴 Negative: {trends.get('negative', 0):.1f}%")
        
        if insights.get("patterns"):
            console.print(f"\n[yellow]Patterns Detected:[/yellow]")
            for pattern in insights["patterns"]:
                console.print(f"  • {pattern}")
        
        if insights.get("recommendation"):
            console.print(f"\n[green]Recommendation:[/green]")
            console.print(f"  {insights['recommendation']}")


def demo_provider_comparison():
    """Demo: Compare different LLM providers"""
    console.print("\n[bold cyan]Demo 4: Provider Comparison[/bold cyan]\n")
    
    client = EnhancedSentimentClient()
    
    text = "The service was okay, nothing special but not terrible either."
    
    console.print(f"[yellow]Comparing providers for:[/yellow] {text}\n")
    
    results = client.compare_providers(text)
    
    table = Table(title="Provider Comparison")
    table.add_column("Provider", style="cyan")
    table.add_column("Sentiment", justify="center")
    table.add_column("Confidence", justify="right")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Status", justify="center")
    
    for provider, result in results.items():
        if "error" in result:
            table.add_row(
                provider.upper(),
                "-",
                "-",
                "-",
                f"[red]Error[/red]"
            )
        else:
            sentiment_color = "green" if result["sentiment"] == "positive" else "red"
            table.add_row(
                provider.upper(),
                f"[{sentiment_color}]{result['sentiment'].upper()}[/{sentiment_color}]",
                f"{result['confidence']:.2%}",
                f"{result['latency_ms']:.0f}",
                "[green]✓[/green]"
            )
    
    console.print(table)
    
    # Show explanations
    for provider, result in results.items():
        if "error" not in result and result.get("explanation") != "N/A":
            console.print(f"\n[bold]{provider.upper()} Explanation:[/bold]")
            console.print(f"  {result['explanation']}")


def demo_multilingual():
    """Demo: Multi-language support"""
    console.print("\n[bold cyan]Demo 5: Multi-Language Analysis[/bold cyan]\n")
    
    client = EnhancedSentimentClient()
    
    texts = {
        "English": "This is absolutely fantastic!",
        "Spanish": "¡Esto es absolutamente fantástico!",
        "French": "C'est absolument fantastique!",
        "German": "Das ist absolut fantastisch!"
    }
    
    table = Table(title="Multi-Language Sentiment Analysis")
    table.add_column("Language", style="cyan")
    table.add_column("Original Text", style="yellow", no_wrap=False)
    table.add_column("Sentiment", justify="center")
    table.add_column("Confidence", justify="right")
    
    for lang, text in texts.items():
        try:
            result = client.analyze_with_insights(text)
            sentiment_color = "green" if result["sentiment"] == "positive" else "red"
            table.add_row(
                lang,
                text,
                f"[{sentiment_color}]{result['sentiment'].upper()}[/{sentiment_color}]",
                f"{result['confidence']:.2%}"
            )
        except Exception as e:
            table.add_row(lang, text, "[red]Error[/red]", "-")
    
    console.print(table)


def main():
    """Run all demos"""
    console.print("\n[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]  Enhanced Sentiment Analysis - Demos     [/bold magenta]")
    console.print("[bold magenta]  Groq & Gemini Integration                [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            console.print("[green]✓ Server is running[/green]\n")
        else:
            console.print("[red]✗ Server is not healthy[/red]\n")
            return
    except Exception as e:
        console.print(f"[red]✗ Cannot connect to server: {e}[/red]\n")
        console.print(f"[yellow]Please start the server: python -m uvicorn app.main:app --port 8001[/yellow]\n")
        return
    
    demos = [
        ("1", "Single Text Analysis", demo_single_analysis),
        ("2", "Negative Feedback Analysis", demo_negative_feedback),
        ("3", "Batch Analysis & Trends", demo_batch_insights),
        ("4", "Provider Comparison", demo_provider_comparison),
        ("5", "Multi-Language Support", demo_multilingual),
    ]
    
    console.print("[yellow]Available Demos:[/yellow]")
    for num, name, _ in demos:
        console.print(f"  {num}. {name}")
    console.print("  0. Run All Demos")
    console.print("  q. Quit\n")
    
    choice = console.input("[bold cyan]Select demo (0-5, q to quit):[/bold cyan] ").strip()
    
    if choice.lower() == 'q':
        console.print("\n[yellow]Goodbye![/yellow]\n")
        return
    
    if choice == '0':
        for _, _, demo_func in demos:
            demo_func()
            console.input("\n[dim]Press Enter to continue...[/dim]\n")
    else:
        for num, _, demo_func in demos:
            if choice == num:
                demo_func()
                break
        else:
            console.print("[red]Invalid choice![/red]")


if __name__ == "__main__":
    main()
