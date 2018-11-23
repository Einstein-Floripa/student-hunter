""" API to look for students that passed in universities entrance exam """

from io import StringIO
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
import os
import hug
import urllib.request
from pdfminer import pdfparser
from scrapy.crawler import CrawlerProcess
from multiprocessing import Process, Pipe
from scrapy.utils.project import get_project_settings
from students_hunter.spiders.student_spider import StudentSpider

example_url_crawl = 'http://dados.coperve.ufsc.br/vestibular2018/resultado1' +\
    '/vestcac03_LinkCursos.html'
example_names_c = 'names=AMANDA%20PEREIRA%20SOARES'


@hug.get('/crawl-ufsc', examples='url='+example_url_crawl+'&'+example_names_c)
def crawl_UFSC(url: hug.types.text, names: hug.types.comma_separated_list):
    """ Crawl url of Federal University of Santa Catarina's entrance exam results,
        searching for listed names."""
    # Pipe for communication between processes
    parent, child = Pipe()
    # Execute crawler in another, avoidind problems with reactor used by scrapy
    p = Process(target=crawl, args=(url, names, child))
    p.start()
    ret = parent.recv()
    p.join()

    return ret


example_url_pdf = 'https://einsteinfloripa.xyz/experimentos/2_Chamada%' + \
    '20UFSC%202018-2.pdf'
example_names_p = 'names=ARTHUR%20JOSÉ%20GIL%20DEJEAN,' + \
                  'gABRIELA%20pAGGI'


@hug.get('/search-pdf', examples='url='+example_url_pdf+'&'+example_names_p)
def search_pdf(url: hug.types.text, names: hug.types.comma_separated_list):
    """ Get pdf from target url, parse it and search by names.""" + \
        """Return list of names"""
    r = urllib.request.urlretrieve(url, 'pdf_file.pdf')
    ret = process('pdf_file.pdf', names)

    os.remove('pdf_file.pdf')
    return ret


def crawl(url, names, conn):
    """ Crawl url of UFSC entrance exam passed as argument """
    process = CrawlerProcess(get_project_settings())

    process.crawl(StudentSpider, start_url=url, names=names)

    process.start()

    conn.send(process.spider_loader._spiders['student'].results)


def process(pdf_file, names):
    content = convert_pdf_to_txt('pdf_file.pdf')

    names_in = []
    for name in names:
        if name.upper() in content:
            names_in.append(name.title())

    return names_in


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    device = TextConverter(rsrcmgr, retstr,
                           codec='utf-8', laparams=LAParams())
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for page in PDFPage.get_pages(fp, set(), maxpages=0,
                                  password="", caching=True,
                                  check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text
