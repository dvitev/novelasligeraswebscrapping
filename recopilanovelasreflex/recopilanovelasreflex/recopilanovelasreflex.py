# """Welcome to Reflex! This file outlines the steps to create a basic app."""

# import reflex as rx

# from rxconfig import config


# class State(rx.State):
#     """The app state."""

#     ...


# def index() -> rx.Component:
#     # Welcome Page (Index)
#     return rx.container(
#         rx.color_mode.button(position="top-right"),
#         rx.vstack(
#             rx.heading("Welcome to Reflex!", size="9"),
#             rx.text(
#                 "Get started by editing ",
#                 rx.code(f"{config.app_name}/{config.app_name}.py"),
#                 size="5",
#             ),
#             rx.link(
#                 rx.button("Check out our docs!"),
#                 href="https://reflex.dev/docs/getting-started/introduction/",
#                 is_external=True,
#             ),
#             spacing="5",
#             justify="center",
#             min_height="85vh",
#         ),
#         rx.logo(),
#     )


# app = rx.App()
# app.add_page(index)


import reflex as rx
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os
import asyncio

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "recopilarnovelas"
COLLECTION_SITIOS = "app_sitio"
COLLECTION_NOVELAS = "app_novela"

def get_mongo_client():
    """Crea y devuelve un nuevo cliente MongoDB"""
    return MongoClient(MONGO_URI)

class State(rx.State):
    loading: bool = False
    sitios: list[dict] = []
    selected_sitio: dict = {}
    novelas: list[dict] = []
    error: str = ""
    
    async def load_home_data(self):
        """Carga la lista de sitios"""
        self.loading = True
        self.error = ""
        try:
            with get_mongo_client() as client:
                db = client[DB_NAME]
                sitios = await asyncio.to_thread(
                    lambda: list(db[COLLECTION_SITIOS].find({}, {'nombre': 1, 'url': 1}))
                )
                self.sitios = sitios
        except Exception as e:
            self.error = f"Error cargando sitios: {str(e)}"
            print(self.error)
        finally:
            self.loading = False

    async def load_sitio_details(self, sitio_id: str):
        """Carga los detalles de un sitio específico"""
        self.loading = True
        self.error = ""
        try:
            with get_mongo_client() as client:
                db = client[DB_NAME]
                
                # Validar y convertir el ID
                try:
                    obj_id = ObjectId(sitio_id)
                except InvalidId:
                    self.error = "ID inválido"
                    return
                
                sitio = await asyncio.to_thread(
                    lambda: db[COLLECTION_SITIOS].find_one({'_id': obj_id})
                )
                
                if not sitio:
                    self.error = "Sitio no encontrado"
                    return
                
                novelas = await asyncio.to_thread(
                    lambda: list(db[COLLECTION_NOVELAS].find(
                        {'sitio_id': sitio_id},
                        {'nombre': 1, 'imagen_url': 1}
                    ))
                )
                
                self.selected_sitio = sitio
                self.novelas = novelas
        except Exception as e:
            self.error = f"Error cargando detalles: {str(e)}"
            print(self.error)
        finally:
            self.loading = False

    async def on_load_sitio_page(self):
        """Manejador para carga de página de detalles"""
        if sitio_id := self.router.params.get("id"):
            await self.load_sitio_details(sitio_id)

def sitio_card(sitio: dict) -> rx.Component:
    """Componente de tarjeta para mostrar un sitio"""
    return rx.card(
        rx.vstack(
            rx.heading(sitio.get('nombre', 'Sin nombre'), size="5"),
            rx.text(sitio.get('url', 'Sin URL'), size="7"),
            rx.divider(),
            rx.link(
                rx.button("Ver novelas", size="7"),
                href=f"/sitio/{str(sitio['_id'])}",
            ),
            spacing="2",
        ),
        width="100%",
        variant="ghost",
        _hover={"box_shadow": "lg"},
    )

def novela_card(novela: dict) -> rx.Component:
    """Componente de tarjeta para mostrar una novela"""
    return rx.card(
        rx.vstack(
            rx.cond(
                novela.get('imagen_url'),
                rx.image(
                    src=novela['imagen_url'],
                    height="200px",
                    object_fit="cover",
                    border_radius="md",
                    alt=f"Portada de {novela.get('nombre', 'novela')}",
                ),
                rx.box(
                    "Imagen no disponible",
                    height="200px",
                    bg="gray.100",
                    border_radius="md",
                    center_content=True,
                )
            ),
            rx.text(novela.get('nombre', 'Sin título'), font_size="7", text_align="center"),
            spacing="2",
        ),
        width="100%",
        variant="ghost",
        _hover={"box_shadow": "md"},
    )

def loading_spinner() -> rx.Component:
    """Componente de carga visual"""
    return rx.center(
        rx.circular_progress(is_indeterminate=True),
        width="100%",
        height="20vh",
    )

def error_message(message: str) -> rx.Component:
    """Muestra mensajes de error"""
    return rx.box(
        rx.hstack(
            rx.icon(tag="warning", color="yellow.500"),
            rx.text(message, color="red.500"),
            bg="red.50",
            padding="3",
            border_radius="md",
            border="1px solid red.100",
        ),
        width="100%",
    )

@rx.page(route="/", on_load=State.load_home_data)
def index() -> rx.Component:
    """Página principal con lista de sitios"""
    return rx.container(
        rx.heading("Sitios de Novelas", size="1", padding_bottom="4"),
        rx.cond(
            State.error,
            error_message(State.error),
            rx.cond(
                State.loading,
                loading_spinner(),
                rx.grid(
                    rx.foreach(State.sitios, sitio_card),
                    columns=[1, 2, 3],
                    gap="4",
                    padding_y="4",
                )
            )
        ),
        max_width="1200px",
        padding="4",
    )

@rx.page(route="/sitio/[id]", on_load=State.on_load_sitio_page)
def sitio_detail() -> rx.Component:
    """Página de detalle de sitio con sus novelas"""
    return rx.container(
        rx.vstack(
            rx.heading("Detalles del Sitio", size="2"),
            rx.button("Volver al inicio", on_click=rx.redirect("/"), margin_bottom="4"),
            
            rx.cond(
                State.error,
                error_message(State.error),
                rx.cond(
                    State.loading,
                    loading_spinner(),
                    rx.fragment(
                        rx.vstack(
                            rx.heading(State.selected_sitio.get('nombre', ''), size="2"),
                            rx.text(f"URL: {State.selected_sitio.get('url', '')}"),
                            rx.text(f"Total de novelas: {len(State.novelas)}"),
                            rx.divider(),
                            rx.heading("Novelas", size="5", padding_top="4"),
                            rx.grid(
                                rx.foreach(State.novelas, novela_card),
                                columns=[2, 3, 4],
                                gap="4",
                                padding_y="4",
                            ),
                            spacing="3",
                        ),
                    )
                )
            ),
            spacing="4",
        ),
        max_width="1200px",
        padding="4",
    )

app = rx.App()
app.add_page(index)
app.add_page(sitio_detail)