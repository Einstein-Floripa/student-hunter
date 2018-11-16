""" Crawl url of Federal University of Santa Catarina's entrance exam results,
    searching for listed names."""

import hug
from scrapy.crawler import CrawlerProcess
from multiprocessing import Process, Pipe
from scrapy.utils.project import get_project_settings
from students_hunter.spiders.student_spider import StudentSpider

example_url = 'http://dados.coperve.ufsc.br/vestibular2018/resultado1' + \
    '/vestcac03_LinkCursos.html'
example_names = 'names=AMANDA%20PEREIRA%20SOARES'


@hug.get('/crawl-ufsc', examples='url='+example_url+'&'+example_names)
def crawl_UFSC(url: hug.types.text, names: hug.types.comma_separated_list):
    # Pipe for communication between processes
    parent, child = Pipe()
    # Execute crawler in another, avoidind problems with reactor used by scrapy
    p = Process(target=crawl, args=(url, names, child))
    p.start()
    ret = parent.recv()
    p.join()

    return ret


def crawl(url, names, conn):
    '''Crawl url searching for names, return
        names and courses in dict by conn'''
    process = CrawlerProcess(get_project_settings())

    process.crawl(StudentSpider, start_url=url, names=names)

    process.start()

    conn.send(process.spider_loader._spiders['student'].results)
