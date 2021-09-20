import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

class Base(object):

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def extract(self):
        print("Starting Extraction")
        results = {}
        try:
            print("Extracting Content")
            results["content"] = self.get_content()

            print("Set Status as Okay")
            results["status"] = "OK"
            results["message"] = ""

        except Exception as e:
            print("Set Status as Error")
            results["status"] = "ERROR"
            results["message"] = str(e)

        finally:
            print("Closing Web Browser")
            self.driver.quit()

        return results

    def get_item(self):
        pass

    def paginate(self):
        pass

    def get_content(self):
        return {}

