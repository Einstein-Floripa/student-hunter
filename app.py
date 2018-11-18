""" API to look for students that passed in universities entrance exam """

import os
import hug
import urllib.request
from tika import parser
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
    """ Download pdf on url and search it for listed names """
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
    content = parser.from_file(pdf_file)['content'].upper()

    names_in = []
    for name in names:
        if name.upper() in content:
            names_in.append(name.title())

    return names_in
