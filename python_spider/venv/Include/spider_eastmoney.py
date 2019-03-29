# coding: utf-8

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Thread, Lock
import os
import csv
import spider
import mysql_operator


# 下面是利用 selenium 抓取html页面的代码

# 初始化函数
def initSpider():
    driver = webdriver.Chrome(executable_path=r"C:\Program Files\Python\Python37\Scripts\chromedriver.exe")
    driver.get("http://fund.eastmoney.com/f10/jjjz_519961.html")  # 要抓取的网页地址

    # 找到"下一页"按钮,就可以得到它前面的一个label,就是总页数
    getPage_text = driver.find_element_by_id("pagebar").find_element_by_xpath(
        "div[@class='pagebtns']/label[text()='下一页']/preceding-sibling::label[1]").get_attribute("innerHTML")
    # 得到总共有多少页
    total_page = int("".join(filter(str.isdigit, getPage_text)))

    # 返回
    return (driver, total_page)


# 获取html内容
def getData(myrange, driver, lock):
    for x in myrange:
        # 锁住
        lock.acquire()

        tonum = driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/input[@class='pnum']")  # 得到 页码文本框
        jumpbtn = driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/input[@class='pgo']")  # 跳转到按钮

        tonum.clear()  # 第x页 输入框
        tonum.send_keys(str(x))  # 去第x页
        jumpbtn.click()  # 点击按钮

        # 抓取
        WebDriverWait(driver, 2000).until(lambda driver: driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/label[@value={0} and @class='cur']".format(x)) != None)

        # 解析得到的html
        bodys = driver.find_element_by_id("jztable").find_element_by_tag_name("tbody")
        trs = bodys.find_elements_by_tag_name("tr")

        for tr in trs:
            tds = tr.find_elements_by_tag_name("td")
            row = [tds[0].text.strip(), tds[1].text.strip(), tds[2].text.strip(), tds[3].text.strip(),
                   tds[4].text.strip(), tds[5].text.strip(), tds[6].text.strip()]
            write("e:/htmls/details/instance.csv", row)

        # 保存到项目中
        # with open("e:/htmls/details/{0}.txt".format(x), 'wb') as f:
        #    f.write(driver.find_element_by_id("jztable").get_attribute("innerHTML").encode('utf-8'))
        #    f.close()

        # 解锁
        lock.release()


# 开始抓取函数
def beginSpider():
    # 初始化爬虫
    (driver, total_page) = initSpider()
    # 创建锁
    lock = Lock()

    r = range(1, int(total_page) + 1)
    step = 10
    range_list = [r[x:x + step] for x in range(0, len(r), step)]  # 把页码分段
    thread_list = []
    for r in range_list:
        t = Thread(target=getData, args=(r, driver, lock))
        thread_list.append(t)
        t.start()
    for t in thread_list:
        t.join()  # 这一步是需要的,等待线程全部执行完成

    print("抓取完成")


def spiderEsatMoney():
    url = "http://fund.eastmoney.com/allfund.html"
    driver = spider.initSpider(url)

    num_moneys = driver.find_elements_by_class_name("num_box")
    for num_money in num_moneys:
        li_funds = num_money.find_elements_by_tag_name("li")
        for li_fund in li_funds:
            a_funds = li_fund.find_elements_by_tag_name("a")
            sub_url = a_funds[0].get_attribute("href")

            get_information(driver, a_funds[0])

            # get_detail( a_funds[0].get_attribute("href"))

            print(a_funds[0].get_attribute("href") + a_funds[0].text)


def get_information(driver, a):
    a.click()

    driver.switch_to.window(driver.window_handles[len(driver.window_handles) - 1])

    WebDriverWait(driver, 100).until(
        lambda driver: driver.find_element_by_xpath("//*[@class='fund_item quotationItem_DataTable popTab']") != None)

    xpaths = driver.find_elements_by_xpath(
        "//*[@class='fund_item quotationItem_DataTable popTab']")

    if (xpaths != None):
        for xpath in xpaths:
            if (xpath.text.find("净值") > -1):
                more = xpath.find_element_by_class_name(
                    "item_more").find_element_by_tag_name("a")
                get_details(driver, more)


def get_details(driver, a):
    driver.execute_script("arguments[0].click();", a)

    driver.switch_to.window(driver.window_handles[len(driver.window_handles) - 1])

    WebDriverWait(driver, 100).until(
        lambda driver: driver.find_element_by_id("pagebar") != None)

    title = driver.find_element_by_class_name("col-left").find_element_by_tag_name("a").text

    refund_name = title[0:title.find("(") - 1]
    refund_id = title[title.find("(") + 1: title.find(")")]

    rate_p = driver.find_element_by_class_name("col-right").find_elements_by_tag_name("p")
    rate_b = rate_p[len(rate_p) - 1].find_elements_by_tag_name("b")
    rate = 0
    if (rate_b != None):
        for rate_fee in rate_b:
            rate_text = rate_fee.text
            if (rate_text.find("%") > 0):
                rate = rate_text[0: rate_text.find("%")]
                break

    mysql_operator.executeSql(None, "INSERT INTO refund (refund_id, refund_name, buy_rate) VALUES ( " + str(int(
        refund_id)) + ", '" + refund_name + "', " + str(rate) + ");")

    # 找到"下一页"按钮,就可以得到它前面的一个label,就是总页数
    getPage_text = driver.find_element_by_id("pagebar").find_element_by_xpath(
        "div[@class='pagebtns']/label[text()='下一页']/preceding-sibling::label[1]").get_attribute("innerHTML")
    # 得到总共有多少页
    total_page = int("".join(filter(str.isdigit, getPage_text)))

    for x in range(1, int(total_page) + 1):

        tonum = driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/input[@class='pnum']")  # 得到 页码文本框
        jumpbtn = driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/input[@class='pgo']")  # 跳转到按钮

        tonum.clear()  # 第x页 输入框
        tonum.send_keys(str(x))  # 去第x页
        jumpbtn.click()  # 点击按钮

        # 抓取
        WebDriverWait(driver, 2000).until(lambda driver: driver.find_element_by_id("pagebar").find_element_by_xpath(
            "div[@class='pagebtns']/label[@value={0} and @class='cur']".format(x)) != None)

        print(x)

        # 解析得到的html
        bodys = driver.find_element_by_id("jztable").find_element_by_tag_name("tbody")
        trs = bodys.find_elements_by_tag_name("tr")

        for tr in trs:
            tds = tr.find_elements_by_tag_name("td")
            print([tds[0].text.strip(), tds[1].text.strip(), tds[2].text.strip(), tds[3].text.strip(),
                   tds[4].text.strip(), tds[5].text.strip(), tds[6].text.strip()])

            if(tds[3].text.trip() != "--"):
                mysql_operator.executeSql(None,
                                          "INSERT INTO refund_details (refund_id, value_date, pure_value, accumulate_value, day_increase_rate, buy_status, sell_status, dividend_distribution) VALUES( "
                                          + refund_id + ",'" + tds[0].text.strip() + "', " + tds[1].text.strip() + ", " + tds[
                                              2].text.strip() + ", " + tds[3].text.strip()[0: tds[3].text.strip().find("%")]
                                          + ",'" + tds[4].text.strip() + "','" + tds[5].text.strip() + "',' "
                                          + tds[6].text.strip() + "')")


spiderEsatMoney()
# beginSpider();

# s = "华夏成长 (000001)"
#
# print(s[0:s.find("(") - 1])
# print(s[s.find("(") + 1: s.find(")")])
