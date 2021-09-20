import time
import datetime
import dateutil.parser
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from . import base

class Lazada(base.Base):

    def __init__(self):
        super().__init__()

    def get_content(self):
        print("Accessing Lazada")
        self.driver.get("https://lazada.sg")
        time.sleep(15)

        self.driver.find_element_by_xpath("//a[@class='card-fs-content-button J_ShopMoreBtn']").click()
        time.sleep(15)

        print("Extraction Completed")
        return self.paginate()

    def paginate(self):
        print("Get Flash Sales Pagination")
        pagination_xpath = "//div[@class='item-list-content clearfix']"
        pagination = self.driver.find_elements_by_xpath(pagination_xpath)

        all_items = []
        for i in range(0, len(pagination)):

            try:
                date = str(datetime.date.today() + datetime.timedelta(days=i))
                date_time = date + " 00:00" 
                sale_datetime = str(dateutil.parser.parse(date_time))

                print("Extracting Flash Sales at : {}".format(sale_datetime))
                all_items.append({"sale_time" : sale_datetime, "sale_items" : self.get_items(i + 1)})

                print("Complete Extracting Flash Sales at: {}".format(sale_datetime))
            except Exception as e:
                print(e)

        print("All Sales Completed Extraction")
        return all_items

    def get_items(self, i):
        loadmore_btm_xpath = "//div[@data-spm='sale-{}']//a[@class='button J_LoadMoreButton']".format(i)
        
        print("Checking Load More Button")
        while len(self.driver.find_elements_by_xpath(loadmore_btm_xpath)) > 0:
            print("Click Button and Sleep 5 secs")
            self.driver.find_element_by_xpath(loadmore_btm_xpath).click()
            time.sleep(5)

        flashsale_card_xpath = "//div[@data-spm='sale-{}']/a".format(i)
        total_items = self.driver.find_elements_by_xpath(flashsale_card_xpath)
        print("Total Items on Sale", len(total_items))

        items = []
        for item in total_items:
            
            print("Item Name")
            try:
                item_name = item.find_element_by_xpath('//div[@class="unit-content"]//div[@class="sale-title"]').text
            except:
                item_name = ''

            print("Item Original Price")
            try:
                item_original_price = item.find_element_by_xpath('//div[@class="unit-content"]//div[@class="origin-price"]//span[@class="origin-price-value"]').text
            except:
                item_original_price = ''

            print("Item Discount Price")
            try:
                item_discounted_price = item.find_element_by_xpath('//div[@class="unit-content"]//div[@class="sale-price"]').text
            except:
                item_discounted_price = ''

            print("Item URL")
            try:
                item_url = item.get_attribute('href')
            except:
                item_url = ''

            items.append({
                "name" : item_name,
                "original_price" : item_original_price, 
                "discounted_price" : item_discounted_price,
                "url" : item_url,
            })
        
        return items