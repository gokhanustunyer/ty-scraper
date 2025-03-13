from scraper import TYScraper

import pandas as pd

def main():
    scraper = TYScraper()
    scraper.startCrawling('results2.xlsx')


if __name__ == '__main__':
    main()