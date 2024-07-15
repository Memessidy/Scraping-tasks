import json
import re
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import aiofiles


class Scraper:
    def __init__(self, urls: list, filename: str):
        self.__urls = urls
        self.__filename = filename
        self.__data = asyncio.Queue()

    async def consume_queue(self):
        items = []
        while not self.__data.empty():
            item = await self.__data.get()
            items.append(item)
            self.__data.task_done()
        return items

    @staticmethod
    async def get_page(url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if not response.ok:
                    raise ValueError(f'Server responded: {response.status}')
                else:
                    soup = BeautifulSoup(await response.text(), 'lxml')
                    print(f"Status: {response.status}")
                    return soup

    async def get_detail_data(self, url: str, soup: BeautifulSoup):
        title = soup.find('h1', {'class': 'x-item-title__mainTitle'}).find('span').text.strip()
        price = soup.find('div', {'data-testid': 'x-price-primary'}).text.strip().split(' ')[1]
        now_available, sold = list(map(lambda x: x.text.strip(), soup.find(
            'div', {'class': 'd-quantity__availability evo'}).find_all('span')))
        sold = sold.split(' ')[0]

        shipping_price = soup.find(
            'div',
            {'class': 'ux-labels-values col-12 ux-labels-values--shipping'}) \
            .find_all('span')[1].text.strip()
        if re.search(shipping_price, r'\d'):
            shipping_price = shipping_price.split(' ')[1]

        soup_seller = soup.find('div', {'class': 'x-sellercard-atf__info__about-seller'})
        link_seller = soup_seller.find('a').get('href')
        seller = soup_seller.get('title')

        little_jpg_images_urls = list(
            map(lambda x: x.get('src'),
                soup.find('div',
                          {'class': 'ux-image-grid-container filmstrip filmstrip-x'}).find_all('img')))

        big_pictures = []
        for pic_num in range(len(little_jpg_images_urls)):
            item = soup.find('div', {'data-idx': pic_num}).find('img').get("src")
            if not item:
                item = soup.find('div', {'data-idx': pic_num}).find('img').get("data-src")
            big_pictures.append(item)

        data = {'title': title, 'price': price, 'shipping_price': shipping_price, 'seller': seller,
                'now available': now_available, 'sold': sold,
                'seller_link': link_seller, 'pics': big_pictures,
                'product_url': url}
        await self.__data.put(data)

    async def write_json(self, data: dict | list):
        async with aiofiles.open(self.__filename, 'a+', encoding='utf-8') as json_file:
            data = json.dumps(data, indent=4)
            await json_file.write(data)

    async def parse(self, product_url: str):
        try:
            soup = await self.get_page(product_url)
            await self.get_detail_data(product_url, soup)
        except Exception as e:
            print(e)
            return

    async def run(self):
        funcs = [asyncio.create_task(self.parse(url)) for url in self.__urls]
        await asyncio.gather(*funcs)
        data_list = await self.consume_queue()
        await self.write_json(data_list)


if __name__ == '__main__':
    url_list = [
        'https://www.ebay.com/itm/296246887870',
        'https://www.ebay.com/itm/285598070672',
        'https://www.ebay.com/itm/186006852125']

    scraper = Scraper(url_list, filename='my_data.json')
    asyncio.run(scraper.run())
