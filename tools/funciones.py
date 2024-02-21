import re
from fpdf import FPDF, HTML2FPDF, TitleStyle
import translators as ts

class PDF(FPDF):
    # HTML2FPDF_CLASS = CustomHTML2FPDF
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Poppins-Regular', size=12)
        self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}}", align="C")

    def chapter_title(self, label):
        self.set_font('Poppins-Regular', size=12)
        self.set_fill_color(200, 220, 255)
        # Printing chapter name:
        self.cell(0, 6, f"{label}", new_x="LMARGIN", new_y="NEXT", align="L", fill=True,)
        # Performing a line break:
        self.ln(4)

    def chapter_body(self, texto):
        self.set_font('Poppins-Regular', size=12)
        # Printing justified text:
        self.write_html(texto)
        # Performing a line break:
        self.ln()

    def add_section(self, title):
        self.start_section(title)

    def print_chapter(self, title, texto):
        self.add_page()
        # self.start_section(title)
        self.chapter_title(title)
        self.chapter_body(texto)


async def traducir(texto):
        """
        Asynchronously translates the given text from English to Spanish using multiple translation services.

        Args:
            texto: The text to be translated.

        Returns:
            The translated text in Spanish.
        """
        contenido_p = ''

        while True:
            try:
                contenido_p = ts.translate_text(
                    texto, translator='bing', from_language='en', to_language='es')
                break
            except Exception as e:
                print(e)
                try:
                    contenido_p = ts.translate_text(
                        texto, translator='google', from_language='en', to_language='es')
                    break
                except Exception as e:
                    print(e)
                    pass
                pass
        return contenido_p

