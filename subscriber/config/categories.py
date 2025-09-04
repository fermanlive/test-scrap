"""
Configuración de categorías válidas para Mercado Libre Uruguay.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Category:
    """Representa una categoría de Mercado Libre Uruguay."""
    id: str
    name: str
    url: str
    description: str


# Mapeo de categorías válidas
VALID_CATEGORIES: Dict[str, Category] = {
    "MLU5725": Category(
        id="MLU5725",
        name="Accesorios para Vehículos",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU5725",
        description="Accesorios y repuestos para vehículos"
    ),
    "MLU1512": Category(
        id="MLU1512",
        name="Agro",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1512",
        description="Productos agropecuarios y agrícolas"
    ),
    "MLU1403": Category(
        id="MLU1403",
        name="Alimentos y Bebidas",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1403",
        description="Comida, bebidas y productos alimenticios"
    ),
    "MLU107": Category(
        id="MLU107",
        name="Animales y Mascotas",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU107",
        description="Productos para mascotas y animales"
    ),
    "MLU1648": Category(
        id="MLU1648",
        name="Antigüedades y Colecciones",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1648",
        description="Antigüedades, arte y colecciones"
    ),
    "MLU1367": Category(
        id="MLU1367",
        name="Arte y Artesanías",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1367",
        description="Arte, manualidades y artesanías"
    ),
    "MLU1144": Category(
        id="MLU1144",
        name="Bebés",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1144",
        description="Productos para bebés y niños pequeños"
    ),
    "MLU1384": Category(
        id="MLU1384",
        name="Belleza y Cuidado Personal",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1384",
        description="Cosméticos, perfumes y cuidado personal"
    ),
    "MLU1039": Category(
        id="MLU1039",
        name="Celulares y Teléfonos",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1039",
        description="Teléfonos móviles y accesorios"
    ),
    "MLU1051": Category(
        id="MLU1051",
        name="Computación",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1051",
        description="Computadoras, laptops y accesorios"
    ),
    "MLU1168": Category(
        id="MLU1168",
        name="Consolas y Videojuegos",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1168",
        description="Videojuegos, consolas y accesorios"
    ),
    "MLU1430": Category(
        id="MLU1430",
        name="Construcción",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1430",
        description="Materiales y herramientas de construcción"
    ),
    "MLU1246": Category(
        id="MLU1246",
        name="Deportes y Fitness",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1246",
        description="Equipamiento deportivo y fitness"
    ),
    "MLU1182": Category(
        id="MLU1182",
        name="Electrodomésticos y Aires Acondicionados",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1182",
        description="Electrodomésticos y climatización"
    ),
    "MLU1276": Category(
        id="MLU1276",
        name="Electrónica, Audio y Video",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1276",
        description="Electrónica de consumo y entretenimiento"
    ),
    "MLU1499": Category(
        id="MLU1499",
        name="Herramientas",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1499",
        description="Herramientas manuales y eléctricas"
    ),
    "MLU1456": Category(
        id="MLU1456",
        name="Hogar, Muebles y Jardín",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1456",
        description="Muebles, decoración y jardín"
    ),
    "MLU1574": Category(
        id="MLU1574",
        name="Industrias y Oficinas",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1574",
        description="Equipamiento industrial y de oficina"
    ),
    "MLU1132": Category(
        id="MLU1132",
        name="Instrumentos Musicales",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1132",
        description="Instrumentos musicales y accesorios"
    ),
    "MLU1196": Category(
        id="MLU1196",
        name="Juegos y Juguetes",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1196",
        description="Juguetes, juegos y entretenimiento"
    ),
    "MLU1215": Category(
        id="MLU1215",
        name="Libros, Revistas y Comics",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1215",
        description="Literatura, revistas y cómics"
    ),
    "MLU1500": Category(
        id="MLU1500",
        name="Música, Películas y Series",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1500",
        description="Entretenimiento audiovisual"
    ),
    "MLU1233": Category(
        id="MLU1233",
        name="Ropa y Accesorios",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1233",
        description="Vestimenta y complementos"
    ),
    "MLU1252": Category(
        id="MLU1252",
        name="Salud y Equipamiento Médico",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1252",
        description="Productos médicos y de salud"
    ),
    "MLU1300": Category(
        id="MLU1300",
        name="Servicios",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1300",
        description="Servicios profesionales y personales"
    ),
    "MLU1318": Category(
        id="MLU1318",
        name="Souvenirs, Cotillón y Fiestas",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1318",
        description="Artículos para fiestas y eventos"
    ),
    "MLU1338": Category(
        id="MLU1338",
        name="Tecnología",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1338",
        description="Tecnología e innovación"
    ),
    "MLU1355": Category(
        id="MLU1355",
        name="Vehículos",
        url="https://www.mercadolibre.com.uy/ofertas?category=MLU1355",
        description="Autos, motos y vehículos"
    ),
}


def get_category_by_id(category_id: str) -> Optional[Category]:
    """
    Obtener una categoría por su ID.
    
    Args:
        category_id: ID de la categoría (ej: MLU5725)
        
    Returns:
        Objeto Category si existe, None si no existe
    """
    return VALID_CATEGORIES.get(category_id.upper())


def get_all_categories() -> List[Category]:
    """
    Obtener todas las categorías válidas.
    
    Returns:
        Lista de todas las categorías disponibles
    """
    return list(VALID_CATEGORIES.values())


def is_valid_category_id(category_id: str) -> bool:
    """
    Verificar si un ID de categoría es válido.
    
    Args:
        category_id: ID de la categoría a validar
        
    Returns:
        True si es válido, False si no
    """
    return category_id.upper() in VALID_CATEGORIES


def validate_category_and_page(category_id: str, page: int) -> tuple[bool, str]:
    """
    Validar tanto la categoría como la página.
    
    Args:
        category_id: ID de la categoría
        page: Número de página
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Validar categoría
    if not category_id:
        return False, "El ID de categoría es requerido"
    
    if not is_valid_category_id(category_id):
        valid_ids = ", ".join([cat.id for cat in get_all_categories()[:5]])
        return False, f"ID de categoría '{category_id}' no válido. IDs válidos incluyen: {valid_ids}..."
    
    # Validar página
    if page < 1:
        return False, "El número de página debe ser mayor o igual a 1"
    
    if page > 1000:  # Límite razonable para páginas
        return False, "El número de página no puede ser mayor a 1000"
    
    return True, ""


def build_category_url(category_id: str, page: int = 1) -> str:
    """
    Construir la URL completa para una categoría y página específica.
    
    Args:
        category_id: ID de la categoría
        page: Número de página (opcional, por defecto 1)
        
    Returns:
        URL completa para la categoría y página
    """
    base_url = "https://www.mercadolibre.com.uy/ofertas"
    
    if page == 1:
        return f"{base_url}?category={category_id.upper()}"
    else:
        return f"{base_url}?category={category_id.upper()}&page={page}"


def get_category_info(category_id: str) -> Optional[Category]:
    """
    Obtener información completa de una categoría.
    
    Args:
        category_id: ID de la categoría
        
    Returns:
        Objeto Category con toda la información
    """
    return get_category_by_id(category_id.upper())
