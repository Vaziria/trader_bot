import functools
import time


def cache_time_func(duration: int):
    cache = {
        'last': 0,
        'hasil': None
    }
    
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwarg):
            now = int(time.time())
            dur = now - cache.get('last')
            if dur > duration:
                cache['last'] = now
                cache['hasil'] = await func(*args, **kwarg)
            
            return cache['hasil']
        return wrapped
    return wrapper



if __name__ == '__main__':
    import asyncio
    import time

    loop = asyncio.get_event_loop()

    class DD:
        @cache_time_func(5)
        async def get_data(self, c = 10):
            print(c)
            return "asdasdad"
    

    async def main():
        dd = DD()
        while True:
            hasil = await dd.get_data(4)
            print(hasil, "asdasd")
            await asyncio.sleep(1)

    loop.run_until_complete(main())