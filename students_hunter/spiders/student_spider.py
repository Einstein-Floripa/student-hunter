import scrapy


class StudentSpider(scrapy.Spider):
    name = 'student'
    start_urls = []
    students = []
    results = []

    def __init__(self, start_url=None, names=[], *args, **kwargs):
        if start_url is None or names == []:
            raise AttributeError("Missing arguments!")
        for name in names:
            self.students.append(name.title())
        self.start_urls.append(start_url)

    def parse(self, response):
        for link in response.css('a::attr(href)'):
            yield response.follow(link, callback=self.parse_course)

    def parse_course(self, response):
        names = []
        course = response.css('font::text').extract_first()
        for i, name in enumerate(response.css('td font::text').extract()):
            # jump even numbers
            if i % 2 == 0:
                continue

            if name.title() in self.students:
                names.append(name.title())
        if names:
            self.results.append({course: names})

        return {course: names}
