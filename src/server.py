# -*- coding: utf-8 -*-

import asyncio
import random

import aiohttp
import requests

from aiohttp import web
from fake_useragent import UserAgent

from db_connector import StorageProxies
from logger import Logger


logger = Logger('proxy_collector')
logger.set_logs('console', message_level='debug')


class ProxyChecker:
    """Checks the health of proxy servers, loads new proxy servers."""
    def __init__(self):
        self.proxy_storage = []
        # 50 this is concurrent connections limit
        self.async_semaphore = asyncio.BoundedSemaphore(50)
        # 10800 == 3 hour
        self.proxy_db = StorageProxies(10800)
        self._min_working_proxies = 100
        self._check_timeout = 30
        self.trust_urls = (
            'http://ebay.com/',
            'http://facebook.com/',
            'http://google.co.uk/',
            'http://google.com/',
            'http://google.de/',
            'http://google.es/',
            'http://google.fr/',
            'http://google.it/',
            'http://google.pl/',
            'http://google.ru/',
            'http://instagram.com/',
            'http://mail.ru/',
            'http://microsoft.com/',
            'http://office.com/',
            'http://ok.ru/',
            'http://twitter.com/',
            'http://vk.com/',
            'http://wikipedia.org/',
            'http://ya.ru/',
            'http://yandex.ru/',
            'http://youtube.com/',
        )

    async def refresh(self):
        """Regular check of the health of proxy servers."""
        while True:
            logger.info('Checking outdated proxies')
            tasks_list = [self.proxy_check(proxy_[0]) for proxy_ in self.proxy_db.get_stale()]
            await asyncio.gather(*tasks_list)

            working_count_proxies = self.proxy_db.working_count()
            logger.info(f'Count actual proxies: {working_count_proxies}')
            if working_count_proxies < self._min_working_proxies:
                await self.fetch_proxy()
            await asyncio.sleep(self._check_timeout)

    async def proxy_check(self, proxy_, check_new_proxy=False):
        """Checks the health of proxy server."""
        logger.debug('Proxy check:', proxy_)
        result = await self._async_check(proxy_)

        if result:
            logger.debug(f'Proxy {proxy_} checked, status: OK')
            if check_new_proxy:
                self.proxy_db.add_new(proxy_)
            else:
                self.proxy_db.update_proxy(proxy_)
        elif not check_new_proxy:
            logger.debug(f'Proxy {proxy_} checked, status: BAD, delete proxy from db')
            self.proxy_db.delete(proxy_)
        else:
            logger.debug(f'Proxy {proxy_} checked, status: BAD')
            # TODO add another table for proxy didn't work

    async def fetch_proxy(self):
        """Receives new proxy servers"""
        logger.info('Running fetch new proxies')
        link_to_proxy_list = 'https://api.proxyscrape.com/'
        payload = {
            'request': 'getproxies',
            'proxytype': 'http',
            'timeout': '3000',
            'country': 'all',
            'ssl': 'all',
            'anonymity': 'all',
        }
        response = requests.get(
            link_to_proxy_list,
            params=payload,
            headers={'User-Agent': UserAgent().random},
        )
        proxy_list = response.text.split('\r\n')

        tasks_list = [
            self.proxy_check(proxy_.strip(), check_new_proxy=True)
            for proxy_ in proxy_list
            if proxy_ and not self.proxy_db.check_availability(proxy_)
        ]
        await asyncio.gather(*tasks_list)

    async def _async_check(self, proxy_):
        """Async ping the proxy server by sending a http request."""
        logger.debug(f'Send request with proxy {proxy_}')
        try:
            return await self._async_request_get(proxy_)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            logger.debug(f'Proxy {proxy_} check Fail: {err}')
            return False

    async def _async_request_get(self, proxy_):
        """Sends an async http get request to the site through a proxy server."""
        logger.debug(f'Async request use proxy: {proxy_}')
        timeout = aiohttp.ClientTimeout(total=5)
        url = random.choice(self.trust_urls)
        async with self.async_semaphore, aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, proxy=f'http://{proxy_}') as resp:
                if resp.status < 400:
                    return True
                return False


class ProxySelector:
    """Selects an random proxy server from the database."""
    def __init__(self):
        # 10800 == 3 hour
        self.proxy_db = StorageProxies(10800)

    async def http_proxy(self, request):
        """Selects an arbitrary http proxy server from the database."""
        proxy_ = self.proxy_db.get_random()
        if proxy_:
            logger.info(f'Send for client ip {request.remote} proxy {proxy_}')
            return web.Response(text=proxy_[0])
        logger.debug(f'Can\'t send find proxy, client ip {request.remote}')
        return web.Response(text='Unfortunately, we can\'t send a proxy sever.')


async def background_tasks(app):
    """Creates a background task."""
    checker = ProxyChecker()
    app['checker'] = asyncio.create_task(checker.refresh())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.slow_callback_duration = 1.5
    loop.set_debug(True)
    proxy = ProxySelector()

    app = web.Application()
    app.add_routes([web.get('/http_proxy', proxy.http_proxy)])
    app.on_startup.append(background_tasks)

    web.run_app(app, port=7878)
