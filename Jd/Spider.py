import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from Jd.config import *
import pymongo



client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10) #设置等待时长

browser.set_window_size(1920,1680)

#实现查询功能
def search():
    print('Searching.......')
    try:
        browser.get('https://www.jd.com')
        #找到输入框
        input  = wait.until(
               EC.presence_of_element_located((By.CSS_SELECTOR, "#key"))
        )
        #找到搜索按钮
        submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#search > div > div.form > button > i'))
        )
        #模拟搜索过程
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > em:nth-child(1)')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


#翻页
def next_page(page_number):
    print('Turning.....', page_number)
    try:

        input  = wait.until(
               EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > input"))
        )
        #找到搜索按钮
        submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > a'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#J_goodsList .gl-warp .gl-item .gl-i-wrap'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


#获取商品信息
def get_products():
    print('Getting......')
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_goodsList .gl-warp .gl-item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#J_goodsList .gl-warp .gl-item').items()
    for item in items:
        product = {
            'href': item.find('.p-img a').attr('href'),
            'image': item.find('.p-img a img').attr('src'),
            'price': item.find('.p-price').text(),
            'commit': item.find('.p-commit').text(),
            'title': item.find('.p-name').text(),
            'shop': item.find('.p-shop').text(),
            'icons': item.find('.p-icons').text()
        }
        print(product)
        save_to_mongo(product)



def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
          print('*********************Save Success**********************/r')
    except Exception:
        print('Save Faile',result)

def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))

    try:
        for i in range(2,total+1):
            next_page(i)
    except Exception:
        next_page(i)

    browser.close()

if __name__ == '__main__':
    main()