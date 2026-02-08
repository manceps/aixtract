"""Command-line interface for AIXtract."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from aixtract import __version__
from aixtract.core.engine import ExtractionEngine, extract
from aixtract.core.registry import ConverterRegistry
from aixtract.models.config import ChunkingConfig, ExtractionConfig

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="aixtract")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """AIXtract - Enterprise document extraction for LLM/NLP pipelines."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="extract")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "text"]),
    default="markdown",
    help="Output format",
)
@click.option("--chunk/--no-chunk", default=False, help="Enable chunking")
@click.option("--chunk-size", type=int, default=1000, help="Chunk size in chars")
@click.option("--chunk-overlap", type=int, default=100, help="Overlap between chunks")
@click.option("-q", "--quiet", is_flag=True, help="Suppress progress output")
def extract_cmd(
    files: tuple[str, ...],
    output: Optional[str],
    output_format: str,
    chunk: bool,
    chunk_size: int,
    chunk_overlap: int,
    quiet: bool,
) -> None:
    """Extract text from documents.

    Examples:

        aixtract extract document.pdf

        aixtract extract *.pdf -o output.md

        aixtract extract report.docx -f json --chunk
    """
    if not files:
        console.print("[red]Error: No files specified[/red]")
        sys.exit(1)

    config = ExtractionConfig(
        output_format=output_format,  # type: ignore[arg-type]
        chunking=ChunkingConfig(
            enabled=chunk,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        ),
    )

    engine = ExtractionEngine(config)
    all_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        for file_path in files:
            task = progress.add_task(
                f"Extracting {Path(file_path).name}...", total=None
            )

            result = engine.extract(file_path)
            all_results.append((file_path, result))

            progress.remove_task(task)

            if result.success:
                if not quiet:
                    console.print(f"[green]OK[/green] {file_path}")
            else:
                console.print(f"[red]FAIL[/red] {file_path}: {result.error}")

    # Output results
    if len(all_results) == 1:
        _, result = all_results[0]
        output_content = _format_output(result, output_format)
    else:
        if output_format == "json":
            output_content = json.dumps(
                [{"file": f, "result": r.model_dump()} for f, r in all_results],
                indent=2,
                default=str,
            )
        else:
            output_content = "\n\n---\n\n".join(
                f"# {Path(f).name}\n\n{r.to_markdown()}"
                for f, r in all_results
                if r.success
            )

    if output:
        Path(output).write_text(output_content)
        console.print(f"[green]Output written to {output}[/green]")
    else:
        click.echo(output_content)


@cli.command()
def formats() -> None:
    """List supported file formats."""
    import aixtract.converters  # noqa: F401 - trigger registration
    converters = ConverterRegistry.list_converters()

    table = Table(title="Supported Formats")
    table.add_column("Converter", style="cyan")
    table.add_column("Extensions", style="green")
    table.add_column("Dependencies", style="yellow")

    for conv in converters:
        table.add_row(
            conv["name"],
            ", ".join(conv["extensions"]),
            ", ".join(conv["requires"]) if conv["requires"] else "none",
        )

    console.print(table)


@cli.command()
@click.argument("url")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "text"]),
    default="markdown",
)
def fetch(url: str, output: Optional[str], output_format: str) -> None:
    """Download and extract from URL.

    Example:

        aixtract fetch https://example.com/doc.pdf -o output.md
    """
    config = ExtractionConfig(output_format=output_format)  # type: ignore[arg-type]

    with console.status(f"Fetching {url}..."):
        result = extract(url, config=config)

    if result.success:
        output_content = _format_output(result, output_format)

        if output:
            Path(output).write_text(output_content)
            console.print(f"[green]Output written to {output}[/green]")
        else:
            click.echo(output_content)
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        sys.exit(1)


def _format_output(result, output_format: str) -> str:
    """Format extraction result for output."""
    if output_format == "json":
        return json.dumps(result.model_dump(), indent=2, default=str)
    elif output_format == "text":
        return result.content
    else:
        return result.to_markdown()


if __name__ == "__main__":
    cli()
