from navigator import Navigator
from scraper import Scraper

if __name__ == "__main__":    
    navigator = Navigator()
    navigator.run(headless=False)
    scraper = Scraper(navigator.page)
    scraper.run()
    input("Press ENTER to close browser")