import flet as ft
import requests
from bs4 import BeautifulSoup as bs
import json


def main(page):
    page.title = "WebScrapping"

    def btn_click(e):
        msg_guardar_ok.visible = False
        msg_guardar_fail.visible = False
        global titulo_datos
        if not txt_name.value:
            txt_name.error_text = "El Campo no puede estar en blanco"
            page.update()
        if "wikipedia.org" not in txt_name.value:
            txt_name.error_text = "La URL no es de Wikipedia. Proporcione una URL de Wikipedia válida."
            page.update()
        else:
            data_obtenida.controls = []
            response = requests.get(txt_name.value)
            response.raise_for_status()

            soup = bs(response.text, 'html.parser')

            titulo = soup.find('h1', id='firstHeading').get_text()
            titulo_datos = titulo
            data_obtenida.controls.append(ft.Text(f"{titulo}"))

            infobox = soup.find(class_='infobox')

            rows = infobox.find_all('tr')
            for row in rows:
                text = '|'.join(r.get_text().strip() for r in row.find_all(['th', 'td']))
                data_obtenida.controls.append(ft.Text(f"| {text} |"))

            content = soup.find_all(id='mw-content-text')[0]
            paragraphs_and_h2s = content.find_all(['p', 'li', 'h2'])

            for tag in paragraphs_and_h2s:
                if tag.name == 'p':
                    data_obtenida.controls.append(ft.Text(tag.get_text()))
                elif tag.name == 'h2':
                    data_obtenida.controls.append(ft.Text(value=""))
                    data_obtenida.controls.append(ft.Text(tag.get_text()))
                elif tag.name == 'li':
                    data_obtenida.controls.append(ft.Text(f"- {tag.get_text()}"))

            data_obtenida.visible = True
            btn_guardar.visible = True
            page.update()

    def save_file_result(e: ft.FilePickerResultEvent):
        global titulo_datos
        try:
            save_file_path.value = e.path + '.json' if e.path else "Cancelled!"
            save_file_path.update()
            if save_file_path.value == "Cancelled!":
                raise
            content = ""
            for do in data_obtenida.controls:
                content += do.__getattribute__('value') + '\n'
            data = {
                "title": titulo_datos,
                "content": content
            }
            with open(save_file_path.value, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            msg_guardar_ok.visible = True
        except Exception as e:
            msg_guardar_fail.visible = True
        page.update()

    txt_name = ft.TextField(label="Ingrese la Url de Wikipedia")
    data_obtenida = ft.ListView(expand=True, spacing=10, visible=False, item_extent=50)
    btn_guardar = ft.ElevatedButton(
        "Guardar Datos",
        visible=False,
        icon=ft.icons.SAVE,
        on_click=lambda _: save_file_dialog.save_file(
            allowed_extensions=['json']
        )
    )
    msg_guardar_ok = ft.Text("Se ha Guardado Correctamente los datos Obtenidos", visible=False)
    msg_guardar_fail = ft.Text("Ha ocurrido un Error al Guardar los Datos Obtenidos", visible=False)
    titulo_datos = ""
    save_file_dialog = ft.FilePicker(on_result=save_file_result)
    save_file_path = ft.Text()

    page.overlay.extend([save_file_dialog])
    page.add(
        txt_name,
        ft.Row(controls=[
            ft.ElevatedButton("Obtener Datos!", on_click=btn_click),
            btn_guardar,
            msg_guardar_ok,
            msg_guardar_fail
        ]),
        ft.Row(controls=[
            save_file_path,
        ]),
        data_obtenida
    )


ft.app(target=main)
