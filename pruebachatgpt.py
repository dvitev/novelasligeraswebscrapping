from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from ebooklib import epub
import requests


def translate_text(text, target_language='es'):
    # Use Google Translate API to translate text to target language
    translate_url = 'https://translation.googleapis.com/language/translate/v2'
    api_key = 'your_google_api_key'
    data = {
        'q': text,
        'target': target_language,
        'format': 'text',
        'key': api_key
    }
    response = requests.post(translate_url, data=data)
    return response.json()['data']['translations'][0]['translatedText']


def convert_pdf_to_epub(pdf_path, epub_path):
    # Extraction of text from PDF using pdfminer
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams(all_texts=True, detect_vertical=True)
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(pdf_path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    # Translation of text using Google Translate API
    # translated_text = translate_text(text)
    translated_text = text

    # Creation of ePub using ebooklib
    book = epub.EpubBook()
    book.set_title("Title")
    book.set_language('es')

    chapter = epub.EpubHtml(title='Introduction', file_name='intro.xhtml', lang='es')
    chapter.content = translated_text
    book.add_item(chapter)

    epub.write_epub(epub_path, book, {})


if __name__ == '__main__':
    pdf_path = '/home/dvitev/Descargas/Isekai Nonbiri Nouka Capítulos 001 al 064.pdf'
    epub_path = 'sample_es.epub'
    convert_pdf_to_epub(pdf_path, epub_path)
