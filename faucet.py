# coding: utf-8

import config

import os
import time
import jinja2
import uvloop
import asyncio
import argparse
import aiohttp_jinja2
from aiohttp import web


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()


SOLANA_KEYPAIR = ".config/faucet.json"


async def faucet_balance():
    proc = await asyncio.create_subprocess_exec(
        "solana", "-ut", "balance", config.TESTNET_FAUCET_ADDR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    balance = stdout.decode()
    return int(balance.split(" SOL")[0])


@aiohttp_jinja2.template("faucet.html")
async def route_faucet(request):
    balance = await faucet_balance()

    return {
        "faucet": {
            "balance": balance,
            "address": config.TESTNET_FAUCET_ADDR
        }
    }


def web_setup(app) -> web.Application:
    """ Configure routes
    """
    app.router.add_route(
        "GET", "/faucet.html", route_faucet, name="faucet")

    app.router.add_route(
        "POST", "/faucet.html", route_faucet)

    return app


async def runtime_context(request):
    """ Append session data to response
    """
    return {
        "current_url": str(request.url),
        "current_host": str(request.host),
        "current_https_url": str(request.url).replace("http://", "https://"),
        "rel_url": request.rel_url
    }


async def handle_error(code, request, response):
    """ Render error404
    """
    code = 404 if code == 404 else 500
    return aiohttp_jinja2.render_template(f"errors/{code}.html", request, {})


async def errors_middleware(app, handler):
    """ Handle exceptions and store in folder
    """
    async def wraps(request):
        try:
            return await handler(request)
        except web.HTTPException as e:
            if e.status == 404:
                return await handle_error(404, request, e)
            else:
                raise
                return await handle_error(500, request, e)
    return wraps


async def timer_middleware(app, handler):
    """ Setup timer middleware
    """
    async def wraps(request):
        t0 = time.time()
        result = await handler(request)
        result.headers["X-Time-Exec"] = "{:.5f}".format(time.time() - t0)
        return result
    return wraps


async def create_app():
    """ Create web application """

    async def setup_jinja2(app) -> web.Application:
        """ Initialize Jinja2
        """
        cache_dir = config.CACHE_JINJA2_DIR
        theme_dir = os.path.abspath("templates")

        if cache_dir:
            if not os.path.exists(config.CACHE_JINJA2_DIR):
                os.mkdir(config.CACHE_JINJA2_DIR, 0o700)

            aiohttp_jinja2.setup(
                app,
                loader=jinja2.FileSystemLoader(theme_dir),
                bytecode_cache=jinja2.FileSystemBytecodeCache(cache_dir),
                context_processors=[
                    runtime_context,
                    aiohttp_jinja2.request_processor
                ]
            )

        aiohttp_jinja2.setup(
            app,
            app_key="uncache",
            loader=jinja2.FileSystemLoader(theme_dir),
            context_processors=[
                runtime_context,
                aiohttp_jinja2.request_processor
            ]
        )

        return app

    app = web.Application(
        middlewares=[
            errors_middleware,
            timer_middleware,
        ]
    )

    app = await setup_jinja2(app)
    app = web_setup(app)
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    host, port = args.host, args.port

    try:
        srv = loop.run_until_complete(create_app())
        web.run_app(srv, host=host, port=port)
    except KeyboardInterrupt:
        loop.close()
