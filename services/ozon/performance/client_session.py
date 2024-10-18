from datetime import datetime

import aiohttp
from multidict import CIMultiDict


class OzonPerformanceClientSession(aiohttp.ClientSession):

    def __init__(self, token_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token_manager = token_manager

    async def _request(self, method, url, **kwargs):
        if (
            self._token_manager.session_token_expired_at is not None
            and self._token_manager.session_token_expired_at < datetime.now()
        ):
            await self._token_manager.refresh_token()

        response = await super()._request(method, url, **kwargs)

        if response.status not in (401, 403):
            return response
        else:
            await self._token_manager.refresh_token()
            await response.release()

            return await super()._request(method, url, **kwargs)

    def set_headers(self, headers):
        self._default_headers = CIMultiDict(headers)
