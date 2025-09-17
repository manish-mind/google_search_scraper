import random
from os.path import join

class UserAgent:
    """
    Class for generating random user agents
    """
    with open("/Users/mind/scraper_tasks/scrapers/resources/chrome_nonmobile.txt", "r") as f:
        agents = f.read().split("\n")[:-1]

    def create_random(self):
        """
        Create a random user agent

        Returns:
            str: A random user agent
        """
        templates = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.{}.{}.{} Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.{}.{}.{} Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.{}.{}.{} Safari/537.36", ]
        a = 0
        b = random.randint(3000, 4000)
        c = random.randint(20, 100)
        return random.choice(templates).format(a, b, c)

    def __init__(self):
        self.UA = self.agents
        self.static = self.random()

    def random(self):
        return random.choice(self.UA)
