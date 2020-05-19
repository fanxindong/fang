# -*- coding: utf-8 -*-
import re

import scrapy
from fang.items import NewHouseItem, ESFHouseItem


class SfwSpider(scrapy.Spider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")
        province = None
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")
            province_td = tds[0]
            province_text = province_td.xpath(".//text()").get()
            province_text = re.sub(r"\s","",province_text)
            if province_text:
                province = province_text
            if province == "其它":
                continue
            city_id = tds[1]
            city_links = city_id.xpath(".//a")
            for city_link in city_links:
                city = city_link.xpath(".//text()").get()
                city_url = city_link.xpath(".//@href").get()
                # print("省份：",province)
                # print("城市：", city)
                # print("城市链接：", city_url)


                #构建新房的url链接
                url_module = city_url.split("//")
                scheme = url_module[0]
                domain_all = url_module[1].split("fang")
                domain_0 = domain_all[0]
                domain_1 = domain_all[1]
                if "bj." in  domain_0:
                    newhouse_url = "https://newhouse.fang.com/house/s/"
                    esf_url = "https://esf.fang.com/"
                else:
                    newhouse_url =scheme + "//" + domain_0 + "newhouse.fang" + domain_1 + "house/s/"
                    # 构建二手房的URL链接
                    esf_url = scheme + "//" + domain_0 + "esf.fang" + domain_1
                # print("城市：%s%s"%(province, city))
                # print("新房链接：%s"%newhouse_url)
                # print("二手房链接：%s"%esf_url)

                # yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={"info":(province, city)})
                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={"info":(province, city)},dont_filter=True)
            #     break
            # break



    def parse_newhouse(self,response):
        province,city = response.meta.get('info')
        lis = response.xpath("//div[contains(@class,'nl_con')]/ul/li")
        for li in lis:

            # 获取 项目名字
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").get()
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").get()
            if name == None:
                pass
            else:
                name = name.strip()
                # print(name)

            # 获取房子类型：几居
            house_type_list = li.xpath(".//div[contains(@class,'house_type')]/a/text()").getall()
            if len(house_type_list) == 0:
                pass
            else:
                house_type_list = list(map(lambda x:re.sub(r"\s","",x),house_type_list))
                rooms = list(filter(lambda x:x.endswith("居"),house_type_list))
                # print(rooms)

            # 获取房屋面积
            area = "".join(li.xpath(".//div[contains(@class,'house_type')]/text()").getall())
            area = re.sub(r"\s|/|－", "", area)
            if len(area) == 0:
                pass
            else:
                area =area
                # print(area)

            # 获取地址
            address = li.xpath(".//div[@class='address']/a/@title").get()
            if address == None:
                pass
            else:
                address = address
                # print(address)

            # 获取区划分：海淀 朝阳
            district_text = "".join(li.xpath(".//div[@class='address']/a//text()").getall())
            if len(district_text) == 0:
                pass
            else:
                district = re.search(r".*\[(.+)\].*",district_text).group(1)
                # print(district)

            # 获取是否在售
            sale = li.xpath(".//div[contains(@class,'fangyuan')]/span/text()").get()
            if sale == None:
                pass
            else:
                sale = sale
                # print(sale)

            # 获取价格
            price = li.xpath(".//div[@class='nhouse_price']//text()").getall()
            if len(price) == 0:
                pass
            else:
                price = "".join(price)
                price = re.sub(r"\s|广告","",price)
                # print(price)

            # 获取网址链接
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").get()
            if origin_url ==None:
                pass
            else:
                origin_url = origin_url
                # print(origin_url)

            item = NewHouseItem(name=name,rooms=rooms,area=area,address=address,district=district,sale=sale,
                                price=price,origin_url=origin_url,province=province,city=city,)
            yield item

        next_url = response.xpath(".//div[@class='page']//a[@class='next']/@href").get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_newhouse,meta={"info":(province,city)})

    def parse_esf(self, response):

        # 获取省份和城市
        province, city = response.meta.get('info')

        dls = response.xpath("//div[@class='shop_list shop_list_4']/dl")
        for dl in dls:
            item = ESFHouseItem(province=province,city=city)
            # 获取小区名字
            name = dl.xpath(".//p[@class='add_shop']/a/text()").get()
            if name == None:
                pass
            else:
                item['name'] = name.strip()
                # print(name)

            # 获取综合信息
            infos = dl.xpath(".//p[@class='tel_shop']/text()").getall()
            if len(infos) == 0:
                pass
            else:
                infos = list(map(lambda x:re.sub(r"\s","",x),infos))
                # print(infos)
                for info in infos:
                    if "厅" in info :
                        item['rooms']= info
                    elif '层' in info:
                        item['floor']= info
                    elif '向' in info:
                        item['toward']=info
                    elif '年' in info:
                        item['year']=info
                    elif '㎡' in info:
                        item['area'] = info
                    # print(item)

            # 获取地址
            address = dl.xpath(".//p[@class='add_shop']/span/text()").get()
            if address == None:
                pass
            else:
                # print(address)
                item['address'] = address

            # 获取总价
            price = dl.xpath("./dd[@class='price_right']/span[1]/b/text()").getall()
            if len(price) == 0:
                pass
            else:
                price="".join(price)
                # print(price)
                item['price'] = price


            # 获取单价
            unit = dl.xpath("./dd[@class='price_right']/span[2]/text()").get()
            if unit == None:
                pass
            else:
                # print(unit)
                item['unit'] = unit

            # 获取初始url
            detail_url = dl.xpath(".//h4[@class='clearfix']/a/@href").get()
            if detail_url == None:
                pass
            else:
                origin_url = response.urljoin(detail_url)
                # print(origin_url)
                item['origin_url'] = origin_url
            # print(item)
            yield item
        next_url = response.xpath(".//div[@class='page_al']/p/a/@href").get()
        # print(next_url)
        yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_esf,meta={"info":(province,city)})














