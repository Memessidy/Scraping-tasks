import aiohttp
import asyncio
import pandas as pd
from tabulate import tabulate


class CountryParser:
    def __init__(self, url: str):
        self.__url = url
        self.__country_data = None

    async def _get_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.__url) as response:
                self.__country_data = await response.json()

    async def _get_table(self):
        countries_data = {'country_name': [], 'country_capital': [], 'country_flag': []}
        for country in self.__country_data:
            countries_data['country_name'].append(country.get('name', {}).get('common'))
            countries_data['country_capital'].append(country.get('capital', [None])[0])
            countries_data['country_flag'].append(country.get('flags', {}).get('png'))

        df = pd.DataFrame.from_dict(countries_data, orient='index')
        df = df.transpose()
        return df

    async def print_table(self):
        await self._get_data()
        df = await self._get_table()
        print(tabulate(df, headers='keys', tablefmt='psql'))


if __name__ == '__main__':
    parser = CountryParser(url='https://restcountries.com/v3.1/all')
    asyncio.run(parser.print_table())
