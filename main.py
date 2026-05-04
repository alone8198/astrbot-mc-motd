import asyncio
import re

from mcstatus import JavaServer, BedrockServer

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

DEFAULT_JE_PORT = 25565
DEFAULT_BE_PORT = 19132


class MCMotdPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("motd")
    async def motd(self, event: AstrMessageEvent):
        '''查询Minecraft服务器MOTD信息。用法: /motd <服务器IP>:<端口> <je/be>，默认JE端口25565，BE端口19132'''
        raw = event.message_str.strip()
        parts = raw.split()
        if parts and parts[0] in ("/motd", "motd"):
            parts = parts[1:]

        if not parts:
            yield event.plain_result(
                "使用方法:\n"
                "/motd <服务器IP>[:端口] <je/be>\n\n"
                "示例:\n"
                "/motd mc.hypixel.net je\n"
                "/motd play.example.com:25565\n"
                "/motd 127.0.0.1 be\n\n"
                "默认端口: Java版 25565  |  基岩版 19132"
            )
            return

        server_addr = parts[0]
        edition = parts[1].lower() if len(parts) >= 2 else "je"

        if edition not in ("je", "be"):
            yield event.plain_result("版本参数错误，请使用 je (Java版) 或 be (基岩版)")
            return

        host, port = self._parse_address(server_addr, edition)
        if host is None:
            yield event.plain_result("端口号格式错误，请输入数字端口")
            return

        logger.info(f"查询Minecraft服务器 {host}:{port} ({'Java' if edition == 'je' else 'Bedrock'})")

        try:
            result = await self._query_server(host, port, edition)
            yield event.plain_result(result)
        except asyncio.TimeoutError:
            yield event.plain_result(f"查询超时: {host}:{port} 无响应，请检查地址是否正确或服务器是否在线")
        except OSError as e:
            yield event.plain_result(f"网络错误: 无法连接到 {host}:{port}\n{self._friendly_error(e)}")
        except Exception as e:
            logger.error(f"查询服务器异常 {host}:{port}: {e}", exc_info=True)
            yield event.plain_result(f"查询失败 {host}:{port}: {str(e)}")

    def _parse_address(self, server_addr: str, edition: str):
        """解析地址，返回 (host, port)。host 为 None 表示解析失败"""
        if server_addr.startswith("["):
            m = re.match(r'\[(.+?)\]:(\d+)$', server_addr)
            if m:
                return m.group(1), int(m.group(2))
            return server_addr.strip("[]"), (DEFAULT_JE_PORT if edition == "je" else DEFAULT_BE_PORT)

        colon_count = server_addr.count(":")
        if colon_count >= 2:
            return server_addr, (DEFAULT_JE_PORT if edition == "je" else DEFAULT_BE_PORT)

        if colon_count == 1:
            host, port_str = server_addr.rsplit(":", 1)
            try:
                return host, int(port_str)
            except ValueError:
                return None, 0

        return server_addr, (DEFAULT_JE_PORT if edition == "je" else DEFAULT_BE_PORT)

    async def _query_server(self, host: str, port: int, edition: str) -> str:
        loop = asyncio.get_running_loop()

        try:
            if edition == "je":
                status = await loop.run_in_executor(
                    None, lambda: JavaServer(host, port).status()
                )
                motd = self._format_motd(status.description)
                latency = round(status.latency, 1)
                version_name = status.version.name

                lines = [
                    "══ Minecraft 服务器状态 ══",
                    f"  服务器: {host}:{port}",
                    f"  版本: Java Edition {version_name}",
                    f"  延迟: {latency}ms",
                    f"  玩家: {status.players.online}/{status.players.max}",
                    f"  MOTD: {motd}",
                    "══════════════════════════",
                ]
            else:
                status = await loop.run_in_executor(
                    None, lambda: BedrockServer(host, port).status()
                )
                motd = self._format_motd(status.description)
                latency = round(status.latency, 1)
                version_name = status.version.name

                lines = [
                    "══ Minecraft 服务器状态 ══",
                    f"  服务器: {host}:{port}",
                    f"  版本: Bedrock Edition {version_name}",
                    f"  延迟: {latency}ms",
                    f"  玩家: {status.players.online}/{status.players.max}",
                    f"  MOTD: {motd}",
                    "══════════════════════════",
                ]
        except asyncio.TimeoutError:
            raise
        except OSError:
            raise
        except Exception:
            raise

        return "\n".join(lines)

    @staticmethod
    def _format_motd(description) -> str:
        """格式化MOTD：支持纯文本、JSON文本组件，清除Minecraft颜色代码"""
        if isinstance(description, str):
            return MCMotdPlugin._strip_color_codes(description.strip())
        if isinstance(description, dict):
            text = MCMotdPlugin._parse_text_component(description)
            return MCMotdPlugin._strip_color_codes(text)
        return str(description)

    @staticmethod
    def _parse_text_component(component) -> str:
        """递归解析Minecraft JSON文本组件"""
        if isinstance(component, str):
            return component
        if isinstance(component, dict):
            text = component.get("text", "")
            for extra_item in component.get("extra", []):
                text += MCMotdPlugin._parse_text_component(extra_item)
            return text
        if isinstance(component, list):
            return "".join(MCMotdPlugin._parse_text_component(c) for c in component)
        return str(component)

    @staticmethod
    def _strip_color_codes(text: str) -> str:
        """移除Minecraft格式化代码（§ + 单字符）"""
        return re.sub(r'[\u00a7\u00A7][0-9a-fA-Fk-oK-OrR]', '', text)

    @staticmethod
    def _friendly_error(exc: OSError) -> str:
        """将OSError转为更友好的描述"""
        msg = str(exc).lower()
        if "refused" in msg:
            return "连接被拒绝，请检查端口是否正确"
        if "timed out" in msg or "timeout" in msg:
            return "连接超时，服务器可能不在线"
        if "no address" in msg or "getaddrinfo" in msg or "name resolution" in msg:
            return "无法解析服务器地址，请检查IP/域名是否正确"
        return str(exc)

    async def terminate(self):
        '''插件卸载时调用'''
        pass
