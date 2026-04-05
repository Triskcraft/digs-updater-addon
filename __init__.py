from asyncio import create_task, sleep
from hashlib import sha256
from hmac import new
from json import dumps, load
from os import getenv, listdir, path
from time import time
from typing import TypedDict, cast

from dotenv import load_dotenv
from mcdis_rcon.classes import McDisClient
from requests import post

MinecraftStats = TypedDict(
    "MinecraftStats",
    {
        "minecraft:mined": dict[str, int],
    },
)


class MinecraftDataStatsJson(TypedDict):
    DataVersion: int
    stats: MinecraftStats


class WebhookData(TypedDict):
    uuid: str
    digs: int


class mdaddon:
    def __init__(self, client: McDisClient) -> None:
        self.client = client
        load_dotenv(".env")

        token = getenv("DIGS_UPDATER_TOKEN")
        if not token:
            print("Skipping addon: DIGS_UPDATER_TOKEN not found in .env")
            return
        self.token = token

        secret = getenv("DIGS_UPDATER_SECRET")
        if not secret:
            print("Skipping addon: DIGS_UPDATER_SECRET not found in .env")
            return
        self.secret = secret

        url = getenv("DIGS_UPDATER_URL")
        if not url:
            print("Skipping addon: DIGS_UPDATER_URL not found in .env")
            return
        self.url = url

        dir_path = getenv("DIGS_UPDATER_PATH")
        if not dir_path:
            print("Skipping addon: DIGS_UPDATER_PATH not found in .env")
            return
        self.dir_path = dir_path

        create_task(self.chron_job())

    async def digs_job(self):
        data: list[WebhookData] = []

        for filename in listdir(self.dir_path):
            if filename.endswith(".json"):
                file_path = path.join(self.dir_path, filename)
                with open(file_path, encoding="utf-8") as f:
                    stats = cast(MinecraftDataStatsJson, load(f))
                    digs = sum(stats["stats"]["minecraft:mined"].values())
                    data.append(WebhookData(uuid=filename[:-5], digs=digs))

        self.send_webhook(data)

    async def chron_job(self):
        while True:
            await self.digs_job()
            await sleep(6 * 60 * 60)

    def send_webhook(self, data: object):
        timestamp = int(time())
        raw_body = dumps(data, separators=(",", ":"))
        signed_payload = f"{timestamp}.{raw_body}"

        signature = new(self.secret.encode(), signed_payload.encode(), sha256).hexdigest()

        headers = {
            "Authorization": f"Bearer {self.token}",
            "x-timestamp": str(timestamp),
            "x-signature": signature,
            "Content-Type": "application/json",
        }

        return post(self.url, data=raw_body, headers=headers)
