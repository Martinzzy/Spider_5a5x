import urllib.request
import urllib.parse
import urllib.error
import os
import pymongo
from lxml import etree

#最简单的反爬取措施
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3377.1 Safari/537.36'}

#配置MongoDB数据库的信息
client = pymongo.MongoClient('localhost')
db = client['5a5x']

#获取总共的页数
def get_page_num(url):
    try:
        req = urllib.request.Request(url,headers=headers)
        html = urllib.request.urlopen(req).read().decode('gbk')
        page_source = etree.HTML(html)
        page_total = str(page_source.xpath('//*[@id="pages"]/b[2]/text()')[0].replace('/',''))
        return page_total
    except urllib.error:
        print('请求初始页失败')
        return None

#获取每篇文章的url
def get_content_url(url):
    try:
        req = urllib.request.Request(url,headers=headers)
        html = urllib.request.urlopen(req).read().decode('gbk')
        #判断是否页面存在有效信息，有的页面提示页数很多，但是有用的不多
        if '没有找到您要访问的页面' not in html:
            page_source = etree.HTML(html)
            content_url = page_source.xpath('//*[@id="main_l"]/dl/dt/a/@href')
            return content_url
        return main()
    except urllib.error:
        print('请求详情页失败')
        return None

#分析详情页的内容，提取title和代码的下载地址
def get_detail_page(url):
    try:
        req = urllib.request.Request(url,headers=headers)
        html = urllib.request.urlopen(req).read().decode('gbk')
        page_source = etree.HTML(html)
        title = page_source.xpath('//*[@id="content"]/table/caption/span/text()')[0]
        download_url = 'http://www.5a5x.com/'+page_source.xpath('//*[@id="down_address"]/a/@href')[0]
        req = urllib.request.Request(download_url,headers=headers)
        content = urllib.request.urlopen(req).read().decode('gbk')
        data = {
            'title':title,
            'url':download_url
        }
        save_to_mongo(data)
        return content,title
    except urllib.error:
        print('获取内容失败')
        return None

#下载代码
def download_code(data,type,title):
    print('正在下载***{}'.format(title))
    with open( type +'/'+ title+'.zip','w') as f:
        f.write(data)
        f.close()

#存储到MongoDB数据库
def save_to_mongo(data):
    if db['code'].insert(data):
        print('存储到MongoDB数据库成功',data)
    else:
        print('存储到MongoDB数据库失败',data)

def main():
    #这是一个易语言源码的所有分类，我们以列表的形式存放
    list_type = ['etools','eimage','emedia','egame','edata','ecom','etrade','enetwork']
    for type in list_type:
        #在当地文件夹中创建相应分析的文件夹
        os.mkdir(type)
        source_url = 'http://www.5a5x.com/wode_source/{}/'.format(type)
        page = get_page_num(source_url)
        for page in range(1, int(page)+1):
            print('正在爬取第{}页'.format(page))
            page_url = 'http://www.5a5x.com/wode_source/{}/{}.html'.format(type,page)
            for url in get_content_url(page_url):
                try:
                    content_url = 'http://www.5a5x.com/' + url
                    print(content_url)
                    content = get_detail_page(content_url)
                    download_code(content[0], type, content[1])
                except TypeError:
                    pass
    #已经建立好的分类的文件夹，我们将其移除列表外
    list_type.remove(type)
    return main()

if __name__ == '__main__':
    main()
