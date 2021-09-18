import time
import pytz
import datetime
import dateutil.parser
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from . import base

class Shopee(base.Base):

    def __init__(self):
        super().__init__()

    def get_content(self):
        print("Accessing Shopee")
        self.driver.get("https://shopee.sg/flash_deals")
        time.sleep(15)

        # ## Click Close on Popup Button 
        # print("Looking for Ad Popup")
        # popup_btn_xpath = "//div[@class='shopee-popup__close-btn']"
        
        # ## If Popup Button Exist Click Close
        # if len(self.driver.find_elements_by_xpath(popup_btn_xpath)) > 0:
        #     print("Closing Ad Popup")
        #     self.driver.find_element_by_xpath(popup_btn_xpath).click()

        # ## Find Flash Sale Link
        # print("Access Flash Sale Page")
        # flash_sale_link_xpath = "//div[@class='shopee-flash-sale-overview-carousel']//a[@class='shopee-header-section__header-link']"
        # self.driver.find_element_by_xpath(flash_sale_link_xpath).click()
        # time.sleep(15)

        print("Extraction Completed")
        return self.paginate()

    def paginate(self):
        print("Get Flash Sales Pagination")
        pagination = list(set([i.get_attribute('href') for i in self.driver.find_elements_by_xpath("//li[@class='image-carousel__item']//a")]))[::-1]

        all_items = []
        for i in pagination:
            self.driver.get(i)
            time.sleep(5)
            
            flashsale_selected_xpath = "//a[@class='flash-sale-session flash-sale-session--selected']"
            flashsale_time_xpath = "{}//div[@class='flash-sale-session__display-hour']".format(flashsale_selected_xpath)
            flashsale_day_xpath = "{}//div[@class='flash-sale-session__display-text']".format(flashsale_selected_xpath)

            sale_day = self.driver.find_element_by_xpath(flashsale_day_xpath).text
            sale_time = self.driver.find_element_by_xpath(flashsale_time_xpath).text

            if sale_day.upper() == 'TOMORROW':
                date = str(datetime.datetime.now(pytz.timezone('Asia/Singapore')).date() + datetime.timedelta(days=1))
                date_time = date + " " + sale_time
                sale_datetime = str(dateutil.parser.parse(date_time))

            else:
                date = str(datetime.datetime.now(pytz.timezone('Asia/Singapore')).date())
                date_time = date + " " + sale_time
                sale_datetime = str(dateutil.parser.parse(date_time))
                

            print("Extracting Flash Sales at : {}".format(sale_datetime))
            all_items.append({"sale_time" : sale_datetime, "sale_items" : self.get_items()})

            print("Complete Extracting Flash Sales at: {}".format(sale_datetime))

        print("All Sales Completed Extraction")
        return all_items

    def get_items(self):
        flashsale_card_xpath = '//div[@class="flash-sale-item-card flash-sale-item-card--landing-page flash-sale-item-card--SG"]'
        page_footer = self.driver.find_element_by_xpath('//footer[@class="Pca2IN _3sSQpy"]')
        
        total_items = []
        while len(total_items) < len(self.driver.find_elements_by_xpath(flashsale_card_xpath)):
            total_items = self.driver.find_elements_by_xpath(flashsale_card_xpath)
            # Hover over page footer to load the dynamically load the rest of page
            ActionChains(self.driver).move_to_element(page_footer).perform()
            time.sleep(5)

        items = []
        for i in range(1, len(total_items) + 1):
            flash_sale_card_i_xpath = '{}[{}]'.format(flashsale_card_xpath, i)

            try:
                item_name = self.driver.find_element_by_xpath('{}//div[@class="flash-sale-item-card__item-name-box"]'.format(flash_sale_card_i_xpath)).text
            except:
                item_name = ''

            try:
                item_original_price = self.driver.find_element_by_xpath('{}//div[@class="flash-sale-item-card__original-price flash-sale-item-card__original-price--landing-page"]//span[@class="item-price-number"]'.format(flash_sale_card_i_xpath)).text
            except:
                item_original_price = ''

            try:
                item_discounted_price = self.driver.find_element_by_xpath('{}//div[@class="flash-sale-item-card__current-price flash-sale-item-card__current-price--landing-page"]//span[@class="item-price-number"]'.format(flash_sale_card_i_xpath)).text
            except:
                item_discounted_price = ''

            try:
                item_url = self.driver.find_element_by_xpath('{}//a[@class="flash-sale-item-card-link"]'.format(flash_sale_card_i_xpath)).get_attribute('href')
            except:
                item_url = ''

            items.append({
                "name" : item_name,
                "original_price" : item_original_price, 
                "discounted_price" : item_discounted_price,
                "url" : item_url,
            })
        
        return items