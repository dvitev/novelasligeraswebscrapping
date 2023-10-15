import os
import json
import requests
import tkinter as tk
from bs4 import BeautifulSoup as bs

def scrape_wikipedia():
    url = entry_url.get()
    # Comprobar si la URL es de Wikipedia
    if "wikipedia.org" not in url:
        result_label.config(text="La URL no es de Wikipedia. Proporcione una URL de Wikipedia válida.")
        return

    try:
        # Realizar la solicitud HTTP a la URL
        response = requests.get(url)
        response.raise_for_status()

        # Analizar el HTML de la página
        soup = bs(response.text, 'html.parser')

        # Obtener el título de la página
        titulo = soup.find('h1', id='firstHeading').get_text()
        result_label.config(text=titulo)

        infobox = soup.find(class_='infobox')
        # Procesa los datos de la tabla
        datainfobox = []

        rows = infobox.find_all('tr')
        for row in rows:
            text = '|'.join(r.get_text().strip() for r in row.find_all(['th', 'td']))
            datainfobox.append('|' + text + '|')

        # Imprime o guarda los datos
        result_text.config(state=tk.NORMAL)
        result_text.delete("1.0", tk.END)
        for row in datainfobox:
            result_text.insert(tk.END, row + "\n")
        result_text.config(state=tk.DISABLED)

        content = soup.find(id='mw-content-text')
        paragraphs_and_h2s = content.find_all(['p', 'li', 'h2'])

        for tag in paragraphs_and_h2s:
            if tag.name == 'p':
                result_text.insert(tk.END, tag.get_text() + "\n")
            elif tag.name == 'h2':
                result_text.insert(tk.END, tag.find('span').get_text() + '\n')
            elif tag.name == 'li':
                result_text.insert(tk.END, '- ' + tag.get_text() + "\n")

    except Exception as e:
        result_label.config(text=f"Ocurrió un error: {str(e}")

# Crear la ventana principal
window = tk.Tk()
window.title("Web Scraping de Wikipedia con Tkinter")

# Crear y configurar los widgets
label_url = tk.Label(window, text="Ingrese la URL de Wikipedia:")
entry_url = tk.Entry(window)
scrape_button = tk.Button(window, text="Scrapear", command=scrape_wikipedia)
result_label = tk.Label(window, text="")
result_text = tk.Text(window, wrap=tk.WORD, state=tk.DISABLED, height=15, width=50)
scrollbar = tk.Scrollbar(window, command=result_text.yview)
result_text.config(yscrollcommand=scrollbar.set)

# Colocar los widgets en la ventana
label_url.grid(row=0, column=0, padx=10, pady=10, sticky='w')
entry_url.grid(row=0, column=1, padx=10, pady=10)
scrape_button.grid(row=1, column=0, columnspan=2, pady=10)
result_label.grid(row=2, column=0, columnspan=2)
result_text.grid(row=3, column=0, columnspan=2, padx=10)
scrollbar.grid(row=3, column=2, sticky='ns')

# Iniciar la aplicación
window.mainloop()
