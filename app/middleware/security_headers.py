from starlette.types import ASGIApp, Scope, Receive, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def add_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                }
                for name, value in security_headers.items():
                    headers = [(k, v) for k, v in headers if k.lower() != name]
                    headers.append((name, value))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, add_security_headers)
