# meta developer: @space_modules
# version: 2.0 beta
# meta banner: https://x0.at/SqAu.png
# requires: openai aiohttp httpx[socks] google-generativeai

import logging
import re
import aiohttp
import asyncio
import io
import time
import random
import httpx

from openai import AsyncOpenAI
import google.generativeai as genai

from .. import loader, utils

logger = logging.getLogger(__name__)


class KeysValidatorMod(loader.Module):
    """
    Массовый чекер API ключей (openai, gemini, grok, claude, deepseek, openrouter).
    """

    strings = {
        "name": "KeysValidator",

        "no_args": (
            "⚠️ <b>Нет ключей!</b>\n"
            "Отправьте ключи текстом, аргументом или ответьте на .txt файл."
        ),
        "downloading": "📥 <b>Скачиваю файл с ключами...</b>",
        "starting": (
            "🚀 <b>Запуск проверки...</b>\n"
            "📦 Ключей: <b>{count}</b>\n"
            "🌐 Прокси: <b>{proxy_mode}</b>\n"
            "🕐 Ожидайте..."
        ),
        "report_caption": (
            "🧬 <b>Отчёт по проверке ключей</b>\n\n"
            "📊 <b>Всего:</b> {total}\n"
            "✅ <b>Рабочих:</b> {alive}\n"
            "💀 <b>Нерабочих:</b> {dead}\n"
            "⏱ <b>Время:</b> {time:.2f} сек\n"
        ),
        "all_good": "🟢 Все ключи рабочие.",
        "all_bad": "🔴 Все ключи нерабочие.",

        "sent_saved": "✅ <b>html-отчёт отправлен в Избранное!</b> (в целях безопасности)",

        "_cfg_use_proxies_doc": "Использовать SOCKS5-прокси при проверке ключей",
        "_cfg_max_proxies_doc": "Максимум отобранных US-прокси",
        "_cfg_proxy_timeout_doc": "Таймаут проверки/использования прокси (секунды)",

        "proxy_refresh_start": (
            "🌐 <b>Обновление списка SOCKS5 USA-прокси. . .</b>\n"
            "🔗 Источников: {sources}"
        ),
        "proxy_refresh_done": (
            "✅ <b>Прокси обновлены.</b>\n"
            "📡 Найдено рабочих USA-прокси: <b>{count}</b>"
        ),
        "proxy_refresh_fail": "❌ Не удалось найти ни одного рабочего US SOCKS5-прокси.",
        "proxy_disabled": (
            "⚠️ Прокси сейчас <b>выключены</b>.\n"
            "Включи их через: <code>.cfg KeysValidator use_proxies</code>"
        ),
    }

    PROXY_SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
        "https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt",
        "https://raw.githubusercontent.com/ArteffKod/socks4/main/socks4%20proxy",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/gitrecon1455/fresh-proxy-list/refs/heads/main/proxylist.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/im-razvan/proxy_list/main/socks5.txt",
        "https://raw.githubusercontent.com/noarche/proxylist-socks5-sock4-exported-updates/main/socks5-online.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/refs/heads/KangProxy/socks5/socks5.txt",
        "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/unknown.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
        "https://raw.githubusercontent.com/themiralay/Proxy-List-World/master/data.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/TuanMinPay/live-proxy/master/socks5.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
        "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
        "https://github.com/zloi-user/hideip.me/raw/refs/heads/master/socks5.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
        "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies/socks5.txt",
        "https://raw.githubusercontent.com/zebbern/Proxy-Scraper/main/socks5.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/unchecked.txt",
        "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/main/socks5.txt",
        "https://raw.githubusercontent.com/FifzzSENZE/Master-Proxy/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/socks5.txt",
        "https://github.com/handeveloper1/Proxy/raw/refs/heads/main/Proxies-Ercin/socks5.txt",
        "https://github.com/Anonym0usWork1221/Free-Proxies/raw/refs/heads/main/proxy_files/socks5_proxies.txt",
        "https://github.com/zenjahid/FreeProxy4u/raw/refs/heads/main/socks5.txt",
        "https://raw.githubusercontent.com/casals-ar/proxy-list/refs/heads/main/socks5",
        "https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/VolkanSah/Auto-Proxy-Fetcher/refs/heads/main/proxies.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/refs/heads/master/proxy_list.txt",
        "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt",
        "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main/socks5.txt",
        "https://raw.githubusercontent.com/variableninja/proxyscraper/refs/heads/main/proxies/socks.txt",
        "https://raw.githubusercontent.com/iniridwanul/Hoot/refs/heads/master/proxylist/socks5.txt",
        "https://raw.githubusercontent.com/iniridwanul/Hoot/refs/heads/master/anonymous-proxylist/socks5.txt",
        "https://raw.githubusercontent.com/joy-deploy/free-proxy-list/refs/heads/main/data/latest/types/socks5/proxies.txt",
        "https://github.com/6Kmfi6HP/proxy_files/raw/refs/heads/main/proxies.txt",
        "https://github.com/murtaja89/public-proxies/raw/refs/heads/main/proxies_all.txt",
        "https://raw.githubusercontent.com/parserpp/ip_ports/refs/heads/main/proxyinfo.txt",
        "https://raw.githubusercontent.com/Vadim287/free-proxy/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/socks5-proxy-list-by-EbraSha.txt",
        "https://raw.githubusercontent.com/casa-ls/proxy-list/refs/heads/main/socks5",
        "https://raw.githubusercontent.com/jetkai/proxy-list/refs/heads/main/online-proxies/txt/proxies-socks5.txt",
    ]

    class Configs:
        class DeepSeek:
            url = "https://api.deepseek.com/v1"
            name = "DeepSeek"
            color = "#4e8cff"
            models = ["deepseek-chat"]

        class Google:
            url = None
            name = "Gemini"
            color = "#34a853"
            models = ["gemini-3.0-pro"]

        class XAI:
            url = "https://api.x.ai/v1"
            name = "Grok"
            color = "#ffffff"
            models = ["grok-beta", "grok-2"]

        class OpenAI:
            url = None
            name = "OpenAI"
            color = "#10a37f"
            models = ["gpt-5", "gpt-4o", "gpt-4o-mini"]

        class OpenRouter:
            url = "https://openrouter.ai/api/v1"
            name = "OpenRouter"
            color = "#7f22ff"
            models = ["openai/gpt-3.5-turbo", "google/gemini-flash-1.5"]

        class Claude:
            url = "https://api.anthropic.com/v1/messages"
            name = "Claude"
            color = "#d97757"
            models = ["claude-3-5-sonnet-20241022"]

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "use_proxies",
                False,
                self.strings["_cfg_use_proxies_doc"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "max_proxies",
                50,
                self.strings["_cfg_max_proxies_doc"],
                validator=loader.validators.Integer(minimum=5, maximum=200),
            ),
            loader.ConfigValue(
                "proxy_timeout",
                7,
                self.strings["_cfg_proxy_timeout_doc"],
                validator=loader.validators.Integer(minimum=3, maximum=30),
            ),
        )
        self.proxies = []
        self.gemini_lock = None

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        saved = self.db.get(self.strings["name"], "proxies", [])
        if isinstance(saved, list):
            self.proxies = saved
        self.gemini_lock = asyncio.Lock()

    def _detect_provider(self, key: str):
        if key.startswith("sk-ant-"):
            return self.Configs.Claude
        if key.startswith("sk-or-"):
            return self.Configs.OpenRouter
        if re.search(r"^AIza", key):
            return self.Configs.Google
        if re.search(r"^xai-", key):
            return self.Configs.XAI
        if re.search(r"^sk-\d{4}", key):
            return self.Configs.DeepSeek
        return self.Configs.OpenAI

    def _parse_proxies_from_text(self, text: str):
        proxies = set()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})", line)
            if m:
                ip, port = m.groups()
                proxies.add(f"{ip}:{port}")
        return proxies

    async def _fetch_proxy_source(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    return ""
                return await resp.text()
        except Exception as e:
            logger.debug(f"Proxy source fetch error {url}: {e}")
            return ""

    async def _test_proxy_country(self, session: aiohttp.ClientSession, addr: str):
        proxy_url = f"socks5://{addr}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["proxy_timeout"])
            async with session.get(
                "https://ipwho.is/",
                proxy=proxy_url,
                timeout=timeout,
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except Exception:
            return None

        if not data.get("success"):
            return None
        if data.get("country_code") != "US":
            return None

        return {
            "proxy": proxy_url,
            "ip": data.get("ip", ""),
            "last_ok": time.time(),
        }

    async def _refresh_proxies(self) -> int:
        max_proxies = self.config["max_proxies"]
        collected = set()
        valid = []

        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            texts = await asyncio.gather(
                *[self._fetch_proxy_source(session, url) for url in self.PROXY_SOURCES]
            )
            for txt in texts:
                collected |= self._parse_proxies_from_text(txt)

            if not collected:
                self.proxies = []
                self.db.set(self.strings["name"], "proxies", self.proxies)
                return 0

            semaphore = asyncio.Semaphore(20)
            tasks = []

            async def worker(addr: str):
                nonlocal valid
                if len(valid) >= max_proxies:
                    return
                async with semaphore:
                    res = await self._test_proxy_country(session, addr)
                    if res and len(valid) < max_proxies:
                        valid.append(res)

            for addr in collected:
                tasks.append(worker(addr))

            await asyncio.gather(*tasks)

        self.proxies = valid
        self.db.set(self.strings["name"], "proxies", self.proxies)
        return len(valid)

    async def _quick_check_proxy(self, session: aiohttp.ClientSession, proxy_url: str) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["proxy_timeout"])
            async with session.get(
                "https://httpbin.org/get",
                proxy=proxy_url,
                timeout=timeout,
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def _get_working_proxy(self, session: aiohttp.ClientSession):
        if not self.config["use_proxies"]:
            return None

        if not self.proxies:
            count = await self._refresh_proxies()
            logger.info(f"Proxy refreshed inside keytest; found {count} US proxies")

        if not self.proxies:
            return None

        for _ in range(min(10, len(self.proxies))):
            entry = random.choice(self.proxies)
            proxy_url = entry.get("proxy")
            if not proxy_url:
                continue

            if time.time() - entry.get("last_ok", 0) < 300:
                return proxy_url

            ok = await self._quick_check_proxy(session, proxy_url)
            if ok:
                entry["last_ok"] = time.time()
                self.db.set(self.strings["name"], "proxies", self.proxies)
                return proxy_url
            else:
                try:
                    self.proxies.remove(entry)
                except ValueError:
                    pass
                self.db.set(self.strings["name"], "proxies", self.proxies)

        return None

    async def _check_gemini_key(self, key: str):
        async with self.gemini_lock:

            def _worker():
                try:
                    genai.configure(api_key=key)
                    model_name = "gemini-1.5-flash"
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content("hi")
                    if resp:
                        return True, model_name, None
                    return False, None, "Пустой ответ от API"
                except Exception as e:
                    return False, None, str(e)

            ok, model_name, err = await asyncio.to_thread(_worker)

        return ok, model_name, err

    async def _check_key_task(self, key: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
        async with semaphore:
            config = self._detect_provider(key)
            result = {
                "key": key,
                "masked": f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "***",
                "provider": config.name,
                "color": config.color,
                "models": [],
                "is_valid": False,
                "error": None,
            }

            if config.name == "Gemini":
                ok, model_name, err = await self._check_gemini_key(key)
                if ok and model_name:
                    result["is_valid"] = True
                    result["models"].append(model_name)
                else:
                    result["error"] = err or "Неизвестная ошибка Gemini"
                return result

            proxy_url = await self._get_working_proxy(session) if self.config["use_proxies"] else None

            try:
                if config.name == "Claude":
                    headers = {
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    }
                    for model in config.models:
                        try:
                            timeout = aiohttp.ClientTimeout(total=self.config["proxy_timeout"])
                            async with session.post(
                                config.url,
                                headers=headers,
                                json={
                                    "model": model,
                                    "max_tokens": 1,
                                    "messages": [{"role": "user", "content": "Hi"}],
                                },
                                proxy=proxy_url,
                                timeout=timeout,
                            ) as resp:
                                if resp.status == 200:
                                    result["models"].append(model)
                                    result["is_valid"] = True
                                    break
                                else:
                                    if not result["error"]:
                                        try:
                                            data = await resp.json()
                                            msg = data.get("error", {}).get("message", str(resp.status))
                                        except Exception:
                                            msg = str(resp.status)
                                        result["error"] = msg
                                    if resp.status in (401, 403):
                                        break
                        except Exception as e:
                            if not result["error"]:
                                result["error"] = str(e).split(" - ")[0]
                            break

                else:
                    client_kwargs = {"api_key": key, "base_url": config.url}
                    http_client = None
                    if proxy_url:
                        http_client = httpx.AsyncClient(
                            proxies=proxy_url,
                            timeout=self.config["proxy_timeout"],
                        )
                        client_kwargs["http_client"] = http_client

                    client = AsyncOpenAI(**client_kwargs)

                    try:
                        for model in config.models:
                            try:
                                await client.chat.completions.create(
                                    messages=[{"role": "user", "content": "Hi"}],
                                    model=model,
                                    max_tokens=1,
                                    timeout=self.config["proxy_timeout"],
                                )
                                result["models"].append(model)
                                result["is_valid"] = True
                                break
                            except Exception as e:
                                err_str = str(e)
                                if not result["error"]:
                                    result["error"] = err_str.split(" - ")[0]
                                if any(
                                    x in err_str.lower()
                                    for x in ["401", "unauthorized", "invalid api key", "incorrect api key"]
                                ):
                                    break
                    finally:
                        await client.close()
                        if http_client is not None:
                            await http_client.aclose()

            except Exception as e:
                result["error"] = str(e)

            return result

    def _generate_html(self, results, time_taken: float) -> str:
        valid_keys = [r["key"] for r in results if r["is_valid"]]

        all_working_str = "\\n".join(valid_keys).replace("`", "\\`")

        html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отчёт по API‑ключам</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-slate-950 text-slate-50 flex justify-center p-4">
    <div class="w-full max-w-6xl space-y-6">
        <header class="space-y-2">
            <h1 class="text-3xl md:text-4xl font-bold tracking-tight flex items-center gap-2">
                <span>⚡ Отчёт по проверке API‑ключей</span>
            </h1>
            <p class="text-slate-400 text-sm">
                Проверено {len(results)} ключей за {time_taken:.2f} сек.
            </p>
        </header>

        <section class="flex flex-wrap gap-4 items-center">
            <div class="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl px-5 py-3 shadow-lg shadow-black/40 flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <div>
                    <p class="text-xs uppercase tracking-wide text-slate-400">Рабочие ключи</p>
                    <p class="text-2xl font-semibold text-emerald-400">{len(valid_keys)}</p>
                </div>
                <div class="w-px h-10 bg-white/10 hidden sm:block"></div>
                <div>
                    <p class="text-xs uppercase tracking-wide text-slate-400">Нерабочие ключи</p>
                    <p class="text-2xl font-semibold text-rose-400">{len(results) - len(valid_keys)}</p>
                </div>
                <div class="w-px h-10 bg-white/10 hidden sm:block"></div>
                <div>
                    <p class="text-xs uppercase tracking-wide text-slate-400">Всего</p>
                    <p class="text-2xl font-semibold text-sky-400">{len(results)}</p>
                </div>
            </div>

            <button
                class="backdrop-blur-xl bg-emerald-500/90 hover:bg-emerald-400 text-slate-950 font-medium px-5 py-3 rounded-2xl shadow-lg shadow-emerald-900/40 text-sm flex items-center gap-2 transition"
                onclick="copyAllWorking()"
            >
                📋 Скопировать все рабочие ключи
                <span class="inline-flex items-center justify-center text-xs bg-emerald-900/70 text-emerald-100 rounded-full px-2 py-0.5">
                    {len(valid_keys)}
                </span>
            </button>
        </section>

        <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        """

        for res in results:
            status_class = "border-emerald-500/60" if res["is_valid"] else "border-rose-500/60"
            glow = "shadow-emerald-900/50" if res["is_valid"] else "shadow-rose-900/40"
            icon = "✅" if res["is_valid"] else "❌"
            models_html = "".join(
                f'<span class="inline-flex items-center justify-center rounded-full bg-slate-800/70 text-[10px] px-2 py-0.5 mr-1 mb-1">{m}</span>'
                for m in res["models"]
            )
            if not models_html and not res["is_valid"]:
                err_txt = (res["error"] or "Нерабочий ключ")[:160]
                models_html = f'<span class="text-[11px] text-rose-300">{err_txt}</span>'

            html += f"""
            <article class="backdrop-blur-xl bg-white/5 border {status_class} rounded-2xl p-4 shadow-lg {glow} flex flex-col gap-2">
                <div class="flex items-center justify-between gap-3">
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold text-white"
                          style="background-color: {res['color']}">
                        {res['provider']}
                    </span>
                    <span class="text-2xl">{icon}</span>
                </div>
                <div class="font-mono text-[11px] bg-black/30 rounded-lg px-2 py-1 break-all text-slate-100">
                    {res['masked']}
                </div>
                <div class="text-[11px] text-slate-300">
                    {models_html}
                </div>
            </article>
            """

        html += f"""
        </section>

        <footer class="pt-2 pb-4 text-[11px] text-slate-500">
            Отчёт сгенерирован модулем KeysValidator (Heroku юзербот). Данные не отправляются третьим лицам, HTML-файл можно хранить локально.
        </footer>
    </div>

    <script>
        function copyAllWorking() {{
            const keys = `{all_working_str}`;
            if (!keys.trim()) {{
                alert('Нет ни одного рабочего ключа.');
                return;
            }}
            const count = keys.split('\\n').filter(Boolean).length;
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(keys).then(() => {{
                    alert('✅ Скопировано ' + count + ' ключ(ей) в буфер обмена.');
                }}).catch(err => {{
                    console.error('Clipboard error:', err);
                    fallbackCopy(keys, count);
                }});
            }} else {{
                fallbackCopy(keys, count);
            }}
        }}

        function fallbackCopy(text, count) {{
            const el = document.createElement('textarea');
            el.value = text;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert('✅ Скопировано ' + count + ' ключ(ей) (fallback).');
        }}
    </script>
</body>
</html>
"""
        return html

    @loader.command()
    async def refproxies(self, message):
        """Обновить список SOCKS5 US-прокси вручную"""
        if not self.config["use_proxies"]:
            return await utils.answer(message, self.strings["proxy_disabled"])

        msg = await utils.answer(
            message,
            self.strings["proxy_refresh_start"].format(
                sources=len(self.PROXY_SOURCES)
            ),
        )
        try:
            count = await self._refresh_proxies()
        except Exception as e:
            logger.error(f"Proxy refresh error: {e}", exc_info=True)
            return await utils.answer(msg, self.strings["proxy_refresh_fail"])

        if count == 0:
            await utils.answer(msg, self.strings["proxy_refresh_fail"])
        else:
            await utils.answer(
                msg,
                self.strings["proxy_refresh_done"].format(count=count),
            )

    @loader.command()
    async def keytest(self, message):
        """<ключи> или реплай на файл — массовая проверка ключей с HTML-отчётом"""
        keys_input = []
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if reply and reply.document:
            await utils.answer(message, self.strings["downloading"])
            file_data = await self.client.download_file(reply.document, bytes)
            try:
                content = file_data.decode("utf-8", errors="ignore")
                keys_input = content.splitlines()
            except Exception as e:
                return await utils.answer(message, f"❌ Ошибка чтения файла: <code>{e}</code>")
        elif reply and reply.text:
            keys_input = reply.text.splitlines()
        elif args:
            keys_input = args.splitlines()

        keys_input = [k.strip() for k in keys_input if k.strip() and len(k.strip()) > 10]

        if not keys_input:
            return await utils.answer(message, self.strings["no_args"])

        start_time = time.time()
        proxy_mode = "ВКЛ (SOCKS5 US)" if self.config["use_proxies"] else "ВЫКЛ"
        status_msg = await utils.answer(
            message,
            self.strings["starting"].format(
                count=len(keys_input),
                proxy_mode=proxy_mode,
            ),
        )

        if self.config["use_proxies"] and not self.proxies:
            try:
                await self._refresh_proxies()
            except Exception as e:
                logger.error(f"Proxy pre-refresh error: {e}", exc_info=True)

        max_concurrent = 7 if self.config["use_proxies"] else 20
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        async with aiohttp.ClientSession() as session:
            for key in keys_input:
                tasks.append(self._check_key_task(key, session, semaphore))
            results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time
        alive_count = sum(1 for r in results if r["is_valid"])
        dead_count = len(results) - alive_count

        html_content = self._generate_html(results, duration)
        file = io.BytesIO(html_content.encode("utf-8"))
        file.name = f"KeyReport_{int(end_time)}.html"

        base_caption = self.strings["report_caption"].format(
            total=len(results),
            alive=alive_count,
            dead=dead_count,
            time=duration,
        )

        if alive_count == len(results):
            base_caption += "\n" + self.strings["all_good"]
        elif alive_count == 0:
            base_caption += "\n" + self.strings["all_bad"]

        caption = base_caption
        is_public = not message.is_private

        if is_public:
            await self.client.send_file("me", file, caption=caption, force_document=True)
            await utils.answer(status_msg, self.strings["sent_saved"])
        else:
            await self.client.send_file(
                message.chat_id,
                file,
                caption=caption,
                force_document=True,
                reply_to=reply.id if reply else None,
            )
            try:
                await status_msg.delete()
            except Exception:
                pass