import os
import json
import time
from selenium import webdriver
from bs4 import BeautifulSoup as bs

def scrape_wikipedia(url):
    # Comprobar si la URL es de Wikipedia
    if "wikipedia.org" not in url:
        print("La URL no es de Wikipedia. Proporcione una URL de Wikipedia válida.")
        return

    # Inicializar el controlador de Selenium
    # driver.minimize_window()
    driver = webdriver.Chrome()

    try:
        # Navegar a la URL proporcionada
        driver.get(url)

        # time.sleep(2)

        html = driver.page_source
        soup = bs(html, 'html.parser')
        driver.close()

        # Obtener el título de la página
        titulo = soup.find_all('h1',id='firstHeading')[0].get_text()
        print(titulo)

        # Obtener el contenido relevante de la página
        # contenido = soup.find_all(id='content')[0].get_text()
        # print(contenido)
        infobox = soup.find_all(class_='infobox')[0]
        # Procesa los datos de la tabla
        datainfobox = []

        rows = infobox.find_all('tr')
        for row in rows:
            # cells = row.get_text()
            if len(row)>1:
                text = '|'
                for r in row:
                    text += (r.get_text()).rstrip().strip() + '|'
                datainfobox.append(text)
            else:
                datainfobox.append('|'+row.get_text()+'|')

        # Imprime o guarda los datos
        for row in datainfobox:
            print(row)

        content = soup.find_all(id='mw-content-text')[0]
        paragraphs_and_h2s = content.find_all(['p', 'li', 'h2'])

        for tag in paragraphs_and_h2s:
            if tag.name == 'p':
                print(tag.get_text())
            elif tag.name == 'h2':
                print(tag.find_all('span')[0].get_text()+'\n')
            elif tag.name == 'li':
                print('- '+tag.get_text())
        # # Guardar los datos en un archivo JSON
        # filename = title.lower().replace(" ", "_") + ".json"
        # data = {
        #     "title": title,
        #     "content": content
        # }
        # with open(filename, "w", encoding="utf-8") as file:
        #     json.dump(data, file, ensure_ascii=False, indent=4)
        #
        # print(f"Datos extraídos y guardados en {filename}")

    except Exception as e:
        print(f"Ocurrió un error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # url = input("Ingrese la URL de Wikipedia: ")
    # scrape_wikipedia(url)
    scrape_wikipedia('https://es.wikipedia.org/wiki/Instituto_Ecuatoriano_de_Seguridad_Social')
