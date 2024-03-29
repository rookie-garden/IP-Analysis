# encoding: utf-8

"""
同a/ip记录反查域名
"""
import sys
sys.setrecursionlimit(10000)
from datetime import datetime
from bs4 import BeautifulSoup
from driverhandler import DriverHandler
from tldextract import extract
import urllib2
import time
import sys


class BGPSpider(DriverHandler):
    """
    https://bgp.he.net/ip/43.229.6.43#_dns
    """

    def __init__(self, timeout=60):

        DriverHandler.__init__(self,'chrome',max_time=timeout)
        self.result = {}
        self.counter=0
        self.base_url = 'https://bgp.he.net/ip/{ip}#_dns'

    def spider(self, ip):

        self.counter+=1
        if not self.result.get(ip):
            self.result[ip] = {}
            self.result[ip]['cur_time'] = datetime.now()
        url=self.base_url.format(ip=ip)
        domains=set()
        flag=self.open_web(url)
        if flag:
            try:
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
            except Exception, e:
                print "parse error:",str(e)
            else:
                div_tip = soup.find(name='div', attrs={'id': 'dns'})
                if div_tip:
                    a_tips = div_tip.find_all(name='a', title=True)
                    for a_tip in a_tips:
                        domain = a_tip.attrs['title'].strip()
                        domains.add(domain)
        if not flag or self.counter%10==0:
            self.destory_driver()
            self.create_driver()
            self.counter=0
        self.result[ip]['domains']=domains
        result=dict(ip=ip,**self.result[ip])
        del self.result[ip]

        return result


class DomainBigDataSpider(object):
    """
    https://domainbigdata.com/
    """

    def __init__(self, timeout=10,wait_time=1):

        self.result = {}
        self.base_url = 'https://domainbigdata.com/{ip}'
        self.timeout = timeout
        self.wait_time=wait_time

    def spider(self, ip):
        """

        :param ip: 
        :return: 
        """
        domains=set()
        if not self.result.has_key(ip):
            self.result[ip] = {}
            self.result[ip]['cur_time']=datetime.now()
        try:
            response = urllib2.urlopen(self.base_url.format(ip=ip), timeout=self.timeout)
            time.sleep(self.wait_time)
        except Exception, e:
            print "get error:",str(e)
        else:
            try:
                soup = BeautifulSoup(response, 'lxml')
            except Exception,e:
                print "parse error:",str(e)
            else:
                lis = soup.find(name='div', attrs={'id': 'MainMaster_divRptDomainsOnSameIP'})
                if lis:
                    a_tips = lis.find_all(name='a', href=True)
                    domains = domains|set([a_tip.text.strip() for a_tip in a_tips])
        self.result[ip]['domains']=domains
        result = dict(ip=ip, **self.result[ip])
        del self.result[ip]

        return result


class AizhanSpider(object):
    """
    dns.aizhan.com　
    """

    def __init__(self, timeout=5, wait_time=2):

        self.base_url = "https://dns.aizhan.com/%s/%d/"  # 基址
        self.timeout = timeout
        self.wait_time = wait_time

    def spider(self, ip, page_index=0):
        """
        获取页面源
        :param ip: 
        :param page_index: 
        :return:
        """
        if page_index<0:
            print "page index is error!"
            sys.exit(-1)
        # print "spider the %dth page"%(page_index+1)
        if page_index == 0:
            self.page_num = -1
            self.result = {}
        if not self.result.has_key(ip):
            self.result[ip] = {}
            self.result[ip]['cur_time']=datetime.now()
            self.result[ip]['domains']=set()
        if page_index==0 or page_index < self.page_num:
            url = self.base_url % (ip, page_index)
            try:
                response = urllib2.urlopen(url, timeout=self.timeout)
                time.sleep(self.wait_time)  # 等待数据加载
            except Exception, e:
                print "get error:",str(e)
            else:
                try:
                    soup = BeautifulSoup(response, 'lxml')
                except Exception, e:
                    print "parse error:", str(e)
                else:
                    if page_index == 0:
                        ul_tip=soup.find(name='div',attrs={'class':'dns-infos'}).ul
                        if ul_tip:
                            lis=ul_tip.find_all(name='li')
                            if len(lis)==3:
                                domains_num=int(lis[2].span.text.strip())
                                self.page_num=domains_num//20
                                if domains_num%20!=0:self.page_num+=1
                                # print "has %d pages"%self.page_num
                    domains_tip=soup.find_all(name='td',attrs={'class':'domain'})[1:]
                    for domain_tip in domains_tip:
                        domain=domain_tip.a.text.strip()
                        domain=extract(domain).registered_domain
                        if domain:
                            self.result[ip]['domains'].add(domain)
            self.spider(ip,page_index=page_index+1)

        result = self.result[ip]

        return dict(ip=ip, **result)


def exper(ip, spider_id):
    generator, rst = [], []
    if 1 in spider_id:
        bgp=BGPSpider()
        # print bgp.spider(ip)
        generator.append(i for i in bgp.spider(ip)['domains'])
        bgp.destory_driver()
    if 2 in spider_id:
        dbd=DomainBigDataSpider()
        # print dbd.spider(ip)
        generator.append(i for i in dbd.spider(ip)['domains'])
    if 3 in spider_id:
        aizhan=AizhanSpider()
        # print aizhan.spider(ip)
        generator.append(i for i in aizhan.spider(ip)['domains'])
    for domains in generator:
        for domain in domains:
            rst.append(domain)
    return rst


if __name__ == "__main__":
    print exper('59.111.105.5', spider_id=[1, 2, 3])


