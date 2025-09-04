"""
Interfaz de línea de comandos para el scraper de Mercado Libre Uruguay.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from .main import MercadoLibreScraper, quick_scrape
from .models.models import ScrapingConfig
from .utils.utils import generate_filename


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="mercadolibre-scraper")
def cli():
    """
    🚀 Scraper de Mercado Libre Uruguay
    
    Extrae información de productos de las ofertas de Mercado Libre Uruguay
    usando Playwright con configuración anti-detección.
    """
    pass


@cli.command()
@click.option("--url", "-u", 
              default="https://www.mercadolibre.com.uy/ofertas",
              help="URL de la página de ofertas")
@click.option("--max-products", "-m", 
              type=int, default=100,
              help="Número máximo de productos a extraer")
@click.option("--output-format", "-f", 
              type=click.Choice(["csv", "json", "excel"]), 
              default="csv",
              help="Formato de salida")
@click.option("--output-path", "-o", 
              help="Ruta personalizada del archivo de salida")
@click.option("--headless", 
              is_flag=True, 
              help="Ejecutar en modo headless (sin interfaz gráfica)")
@click.option("--delay", "-d", 
              type=float, default=2.0,
              help="Delay entre requests en segundos")
@click.option("--timeout", "-t", 
              type=int, default=30000,
              help="Timeout del navegador en milisegundos")
def scrape(url: str, max_products: int, output_format: str, output_path: Optional[str], 
           headless: bool, delay: float, timeout: int):
    """
    🎯 Extraer ofertas de Mercado Libre Uruguay.
    
    Ejemplos:
        mercadolibre-scraper scrape
        mercadolibre-scraper scrape --max-products 50 --output-format json
        mercadolibre-scraper scrape --url "https://www.mercadolibre.com.uy/ofertas" --headless
    """
    console.print(Panel.fit(
        f"[bold blue]🚀 Iniciando Scraping[/bold blue]\n"
        f"URL: [cyan]{url}[/cyan]\n"
        f"Productos objetivo: [green]{max_products}[/green]\n"
        f"Formato: [yellow]{output_format.upper()}[/yellow]\n"
        f"Modo: [red]{'Headless' if headless else 'Con interfaz'}[/red]",
        title="Configuración del Scraping"
    ))
    
    # Configurar scraper
    config = ScrapingConfig(
        headless=headless,
        timeout=timeout,
        max_products=max_products,
        delay_between_requests=delay,
        output_format=output_format
    )
    
    # Generar ruta de salida si no se especifica
    if not output_path:
        filename = generate_filename("ofertas", output_format)
        output_path = Path("output") / filename
    
    # Ejecutar scraping
    asyncio.run(_run_scraping(config, url, output_path))


async def _run_scraping(config: ScrapingConfig, url: str, output_path: Path):
    """Ejecutar el scraping con barra de progreso."""
    scraper = MercadoLibreScraper(config)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extrayendo productos...", total=None)
            
            # Ejecutar scraping
            result = await scraper.scrape_ofertas(url, config.max_products)
            
            progress.update(task, description="Exportando datos...")
            
            # Exportar productos
            export_path = await scraper.scrape_and_export(
                url=url,
                max_products=config.max_products,
                output_format=config.output_format,
                output_path=str(output_path)
            )
            
            progress.update(task, description="Completado!", completed=True)
        
        # Mostrar resultados
        _display_results(result, export_path)
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error en el scraping:[/bold red] {e}")
        sys.exit(1)
    
    finally:
        await scraper.close()


def _display_results(result, export_path: str):
    """Mostrar resultados del scraping."""
    console.print("\n" + "="*60)
    
    # Estadísticas generales
    stats_table = Table(title="📊 Estadísticas del Scraping")
    stats_table.add_column("Métrica", style="cyan")
    stats_table.add_column("Valor", style="green")
    
    stats_table.add_row("Total de productos", str(result.total_products))
    stats_table.add_row("Extracciones exitosas", str(result.successful_scrapes))
    stats_table.add_row("Errores", str(result.failed_scrapes))
    stats_table.add_row("Tasa de éxito", f"{result.success_rate:.1f}%")
    stats_table.add_row("Duración", f"{result.duration:.1f} segundos")
    
    console.print(stats_table)
    
    # Información del archivo
    console.print(f"\n[bold green]✅ Scraping completado exitosamente![/bold green]")
    console.print(f"📁 Archivo generado: [cyan]{export_path}[/cyan]")
    
    # Mostrar algunos productos como ejemplo
    if result.products:
        console.print("\n[bold yellow]📋 Muestra de productos extraídos:[/bold yellow]")
        
        sample_table = Table(show_header=True, header_style="bold magenta")
        sample_table.add_column("Título", style="cyan", max_width=40)
        sample_table.add_column("Precio", style="green")
        sample_table.add_column("Vendedor", style="yellow")
        sample_table.add_column("Rating", style="blue")
        
        for product in result.products[:5]:  # Mostrar solo 5 productos
            title = product.title[:37] + "..." if len(product.title) > 40 else product.title
            price = f"${product.current_price:,.0f}"
            rating = f"{product.rating:.1f}" if product.rating else "N/A"
            
            sample_table.add_row(title, price, product.seller, rating)
        
        console.print(sample_table)


@cli.command()
@click.option("--url", "-u", required=True,
              help="URL del producto a extraer")
@click.option("--output-format", "-f", 
              type=click.Choice(["csv", "json", "excel"]), 
              default="json",
              help="Formato de salida")
@click.option("--output-path", "-o", 
              help="Ruta personalizada del archivo de salida")
@click.option("--headless", 
              is_flag=True, 
              help="Ejecutar en modo headless")
def product(url: str, output_format: str, output_path: Optional[str], headless: bool):
    """
    🔍 Extraer detalles completos de un producto específico.
    
    Ejemplos:
        mercadolibre-scraper product --url "https://www.mercadolibre.com.uy/..."
        mercadolibre-scraper product --url "..." --output-format json
    """
    console.print(Panel.fit(
        f"[bold blue]🔍 Extrayendo Producto[/bold blue]\n"
        f"URL: [cyan]{url}[/cyan]\n"
        f"Formato: [yellow]{output_format.upper()}[/yellow]",
        title="Extracción de Producto Individual"
    ))
    
    # Generar ruta de salida si no se especifica
    if not output_path:
        filename = generate_filename("producto", output_format)
        output_path = Path("output") / filename
    
    # Ejecutar extracción
    asyncio.run(_run_product_extraction(url, output_format, output_path, headless))


async def _run_product_extraction(url: str, output_format: str, output_path: Path, headless: bool):
    """Ejecutar extracción de producto individual."""
    config = ScrapingConfig(
        headless=headless,
        max_products=1,
        output_format=output_format
    )
    
    scraper = MercadoLibreScraper(config)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extrayendo producto...", total=None)
            
            # Extraer producto
            products = await scraper.scrape_product_details([url])
            
            if not products:
                raise Exception("No se pudo extraer el producto")
            
            progress.update(task, description="Exportando datos...")
            
            # Exportar producto
            export_path = scraper.utils.export_products(
                [products[0].to_dict()],
                str(output_path),
                output_format
            )
            
            progress.update(task, description="Completado!", completed=True)
        
        # Mostrar resultados
        product = products[0]
        console.print(f"\n[bold green]✅ Producto extraído exitosamente![/bold green]")
        console.print(f"📁 Archivo generado: [cyan]{export_path}[/cyan]")
        
        # Mostrar detalles del producto
        details_table = Table(title="📋 Detalles del Producto")
        details_table.add_column("Campo", style="cyan")
        details_table.add_column("Valor", style="green")
        
        details_table.add_row("Título", product.title)
        details_table.add_row("Precio", f"${product.current_price:,.0f}")
        details_table.add_row("Vendedor", product.seller)
        details_table.add_row("Rating", f"{product.rating:.1f}" if product.rating else "N/A")
        details_table.add_row("Reviews", str(product.review_count) if product.review_count else "N/A")
        details_table.add_row("Envío gratis", "Sí" if product.free_shipping else "No")
        
        if product.brand:
            details_table.add_row("Marca", product.brand)
        if product.condition:
            details_table.add_row("Condición", product.condition)
        if product.seller_location:
            details_table.add_row("Ubicación", product.seller_location)
        
        console.print(details_table)
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error al extraer producto:[/bold red] {e}")
        sys.exit(1)
    
    finally:
        await scraper.close()


@cli.command()
@click.option("--url", "-u", 
              default="https://www.mercadolibre.com.uy/ofertas",
              help="URL de la página de ofertas")
@click.option("--max-products", "-m", 
              type=int, default=20,
              help="Número máximo de productos a extraer")
@click.option("--headless", 
              is_flag=True, 
              help="Ejecutar en modo headless")
def preview(url: str, max_products: int, headless: bool):
    """
    👀 Vista previa rápida de productos sin exportar.
    
    Ejemplos:
        mercadolibre-scraper preview
        mercadolibre-scraper preview --max-products 10
    """
    console.print(Panel.fit(
        f"[bold blue]👀 Vista Previa[/bold blue]\n"
        f"URL: [cyan]{url}[/cyan]\n"
        f"Productos: [green]{max_products}[/green]",
        title="Vista Previa Rápida"
    ))
    
    # Ejecutar vista previa
    asyncio.run(_run_preview(url, max_products, headless))


async def _run_preview(url: str, max_products: int, headless: bool):
    """Ejecutar vista previa de productos."""
    config = ScrapingConfig(
        headless=headless,
        max_products=max_products
    )
    
    scraper = MercadoLibreScraper(config)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extrayendo vista previa...", total=None)
            
            # Extraer productos
            result = await scraper.scrape_ofertas(url, max_products)
            
            progress.update(task, description="Completado!", completed=True)
        
        # Mostrar vista previa
        if result.products:
            console.print(f"\n[bold green]✅ Vista previa completada![/bold green]")
            console.print(f"📊 Productos extraídos: [cyan]{len(result.products)}[/cyan]")
            
            # Tabla de productos
            preview_table = Table(title="📋 Vista Previa de Productos")
            preview_table.add_column("#", style="cyan")
            preview_table.add_column("Título", style="green", max_width=50)
            preview_table.add_column("Precio", style="yellow")
            preview_table.add_column("Descuento", style="red")
            preview_table.add_column("Vendedor", style="blue", max_width=20)
            
            for i, product in enumerate(result.products, 1):
                title = product.title[:47] + "..." if len(product.title) > 50 else product.title
                price = f"${product.current_price:,.0f}"
                discount = f"{product.discount_percentage:.0f}%" if product.discount_percentage else "N/A"
                seller = product.seller[:17] + "..." if len(product.seller) > 20 else product.seller
                
                preview_table.add_row(str(i), title, price, discount, seller)
            
            console.print(preview_table)
            
            # Estadísticas rápidas
            stats = scraper.get_statistics(result)
            if stats:
                console.print(f"\n[bold yellow]📈 Estadísticas Rápidas:[/bold yellow]")
                console.print(f"Precio promedio: [green]${stats['avg_price']:,.0f}[/green]")
                console.print(f"Descuento promedio: [red]{stats['avg_discount']:.1f}%[/red]")
                console.print(f"Rating promedio: [blue]{stats['avg_rating']:.1f}[/blue]")
                console.print(f"Envío gratis: [cyan]{stats['free_shipping_percentage']:.1f}%[/cyan]")
        
        else:
            console.print("\n[bold red]❌ No se pudieron extraer productos[/bold red]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error en la vista previa:[/bold red] {e}")
        sys.exit(1)
    
    finally:
        await scraper.close()


@cli.command()
def config():
    """
    ⚙️ Mostrar configuración actual del scraper.
    """
    console.print(Panel.fit(
        "[bold blue]⚙️ Configuración del Scraper[/bold blue]\n"
        "Para personalizar la configuración, crea un archivo .env\n"
        "o modifica las variables de entorno correspondientes.",
        title="Configuración"
    ))
    
    # Mostrar configuración por defecto
    config = ScrapingConfig()
    
    config_table = Table(title="🔧 Configuración por Defecto")
    config_table.add_column("Parámetro", style="cyan")
    config_table.add_column("Valor", style="green")
    config_table.add_column("Variable de Entorno", style="yellow")
    
    config_table.add_row("URL de ofertas", config.offers_url, "N/A")
    config_table.add_row("Modo headless", str(config.headless), "BROWSER_HEADLESS")
    config_table.add_row("Timeout (ms)", str(config.timeout), "BROWSER_TIMEOUT")
    config_table.add_row("Productos máx.", str(config.max_products), "MAX_PRODUCTS")
    config_table.add_row("Delay (seg)", str(config.delay_between_requests), "DELAY_BETWEEN_REQUESTS")
    config_table.add_row("Reintentos", str(config.retry_attempts), "RETRY_ATTEMPTS")
    config_table.add_row("Formato salida", config.output_format, "OUTPUT_FORMAT")
    config_table.add_row("Directorio salida", config.output_dir, "OUTPUT_DIR")
    
    console.print(config_table)
    
    # Mostrar ejemplo de archivo .env
    env_example = """
# Ejemplo de archivo .env
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30000
MAX_PRODUCTS=100
DELAY_BETWEEN_REQUESTS=2.0
RETRY_ATTEMPTS=3
OUTPUT_FORMAT=csv
OUTPUT_DIR=output
"""
    
    console.print(Panel(env_example, title="📝 Ejemplo de archivo .env"))


@cli.command()
def install():
    """
    🔧 Instalar dependencias y navegadores necesarios.
    """
    console.print(Panel.fit(
        "[bold blue]🔧 Instalación de Dependencias[/bold blue]\n"
        "Este comando instalará las dependencias necesarias\n"
        "y los navegadores de Playwright.",
        title="Instalación"
    ))
    
    # Ejecutar instalación
    asyncio.run(_run_install())


async def _run_install():
    """Ejecutar la instalación de dependencias."""
    try:
        # Instalar dependencias con Poetry
        console.print("[yellow]📦 Instalando dependencias con Poetry...[/yellow]")
        result = await asyncio.create_subprocess_exec(
            "poetry", "install",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.communicate()
        
        if result.returncode == 0:
            console.print("[green]✅ Dependencias instaladas correctamente[/green]")
        else:
            console.print("[red]❌ Error al instalar dependencias[/red]")
            return
        
        # Instalar navegadores de Playwright
        console.print("[yellow]🌐 Instalando navegadores de Playwright...[/yellow]")
        result = await asyncio.create_subprocess_exec(
            "poetry", "run", "playwright", "install",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.communicate()
        
        if result.returncode == 0:
            console.print("[green]✅ Navegadores instalados correctamente[/green]")
        else:
            console.print("[red]❌ Error al instalar navegadores[/red]")
            return
        
        console.print("\n[bold green]🎉 Instalación completada exitosamente![/bold green]")
        console.print("Ahora puedes usar el scraper con: [cyan]mercadolibre-scraper scrape[/cyan]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error durante la instalación:[/bold red] {e}")
        sys.exit(1)


def main():
    """Función principal del CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️ Operación cancelada por el usuario[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error inesperado:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
