import os
import requests
import logging
from datetime import datetime
import aiohttp
import ssl
from aiohttp import ClientConnectorCertificateError
from requests.exceptions import SSLError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._session = None
        self.verify_ssl = True

    # ------------------------------------------------------------------
    # Message builders (shared by sync/async senders to avoid duplication)
    # ------------------------------------------------------------------

    def _format_position_opened(self, symbol, side, entry_price, size, leverage,
                                 stop_loss=None, take_profit=None, ml_score=None):
        direction = "COMPRA" if side == "BUY" else "VENDA"

        details = (
            "<b>POSICAO ABERTA</b>\n\n"
            f"<b>Par:</b> {symbol}\n"
            f"<b>Direcao:</b> {direction}\n"
            f"<b>Preco de Entrada:</b> ${entry_price:.4f}\n"
            f"<b>Tamanho:</b> ${size:.2f} USDT\n"
            f"<b>Alavancagem:</b> {leverage}x\n"
            f"<b>Horario:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        extras = []
        if ml_score is not None:
            extras.append(f"<b>Score ML:</b> {ml_score:.2f}")
        if stop_loss is not None:
            extras.append(f"<b>Stop Loss:</b> ${stop_loss:.4f}")
        if take_profit is not None:
            extras.append(f"<b>Take Profit:</b> ${take_profit:.4f}")

        if extras:
            details += "\n" + "\n".join(extras)

        return details

    def _format_position_closed(self, symbol, side, entry_price, exit_price, pnl, roe, reason=None):
        pnl_value = float(pnl) if pnl is not None else 0.0
        roe_value = float(roe) if roe is not None else 0.0
        entry = float(entry_price) if entry_price is not None else 0.0
        exit_val = float(exit_price) if exit_price is not None else 0.0

        is_profit = pnl_value > 0
        result = "Ganhou" if is_profit else "Perdeu"
        direction = "COMPRA" if side == "BUY" else "VENDA"
        reason_text = f"\n<b>Motivo:</b> {reason}" if reason else ""

        return (
            "<b>POSICAO FECHADA</b>\n\n"
            f"<b>{direction}</b> | {symbol}\n"
            f"<b>{result}:</b> ${abs(pnl_value):.2f} USDT ({roe_value:+.2f}% ROE)\n"
            f"<b>Entrada:</b> ${entry:.4f}\n"
            f"<b>Saida:</b> ${exit_val:.4f}{reason_text}\n"
            f"<b>Horario:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

    def _bot_started_message(self):
        return (
            "[BOT] Trading iniciado!\n\n"
            "Monitorando o mercado e procurando oportunidades."
        )

    def _bot_stopped_message(self):
        return (
            "[BOT] Trading parado.\n\n"
            "O bot foi desativado."
        )

    def _bot_observing_message(self, note=None):
        message = (
            "[BOT] Em observacao.\n\n"
            "Analisando o mercado e aguardando sinais confiaveis."
        )
        if note:
            message += f"\n\n{note}"
        return message

    async def close(self):
        """Dispose internal HTTP session (useful for reloads/shutdown)"""
        if self._session:
            await self._session.close()
            self._session = None

    def initialize(self, bot_token=None, chat_id=None, verify_ssl=None):
        """Initialize Telegram notifier"""
        if bot_token is not None:
            self.bot_token = bot_token.strip()
        if chat_id is not None:
            self.chat_id = str(chat_id).strip()
        if verify_ssl is not None:
            self.verify_ssl = bool(verify_ssl)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        return True

    def send_message(self, message, _retry_on_ssl_error=True):
        """Send a message to Telegram (sync version for compatibility)"""
        try:
            if not self.bot_token or not self.chat_id:
                logger.warning("Telegram not configured, skipping notification")
                return False

            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(
                url,
                json=payload,
                timeout=10,
                verify=self.verify_ssl
            )
            if response.status_code != 200:
                logger.warning(
                    "Telegram HTTP %s - Body: %s",
                    response.status_code,
                    response.text[:200]
                )
            return response.status_code == 200

        except SSLError as exc:
            if self.verify_ssl and _retry_on_ssl_error:
                logger.warning(
                    "Telegram SSL verification failed (%s). Retrying without certificate validation.",
                    exc,
                )
                self.verify_ssl = False
                return self.send_message(message, _retry_on_ssl_error=False)
            logger.error("Error sending Telegram message due to SSL issue: %s", exc)
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def _create_session(self):
        """Create aiohttp session honoring SSL configuration."""
        if self.verify_ssl:
            return aiohttp.ClientSession()

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        return aiohttp.ClientSession(connector=connector)

    async def send_message_async(self, message, _retry_on_ssl_error=True):
        """Send a message to Telegram (async non-blocking)"""
        try:
            if not self.bot_token or not self.chat_id:
                logger.debug("Telegram not configured, skipping notification")
                return False

            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            # Criar sessao se nao existir; honra configuracao de SSL
            if not self._session or self._session.closed:
                self._session = self._create_session()

            async with self._session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    body = await response.text()
                    logger.warning("Telegram HTTP %s - Body: %s", response.status, body[:200])
                    return False

        except ClientConnectorCertificateError as exc:
            if self.verify_ssl and _retry_on_ssl_error:
                logger.warning(
                    "Telegram SSL verification failed (%s). Retrying without certificate validation.",
                    exc,
                )
                await self.close()
                self.verify_ssl = False
                return await self.send_message_async(message, _retry_on_ssl_error=False)
            logger.error("Error sending async Telegram message due to SSL issue: %s", exc)
            return False
        except Exception as e:
            logger.error(f"Error sending async Telegram message: {e}")
            return False

    def notify_position_opened(self, symbol, side, entry_price, size, leverage,
                               stop_loss=None, take_profit=None, ml_score=None):
        """Notify when position is opened"""
        message = self._format_position_opened(symbol, side, entry_price, size, leverage, stop_loss, take_profit, ml_score)
        return self.send_message(message)

    async def notify_position_opened_async(self, symbol, side, entry_price, size, leverage,
                                           stop_loss=None, take_profit=None, ml_score=None):
        message = self._format_position_opened(symbol, side, entry_price, size, leverage, stop_loss, take_profit, ml_score)
        return await self.send_message_async(message)

    def notify_position_closed(self, symbol, side, entry_price, exit_price, pnl, roe, reason=None):
        """Notify when position is closed"""
        try:
            message = self._format_position_closed(symbol, side, entry_price, exit_price, pnl, roe, reason)
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Error formatting position closed notification: {e}")
            try:
                simple_message = f"POSICAO FECHADA: {symbol} | PnL: {pnl if pnl else 0.0}"
                return self.send_message(simple_message)
            except Exception:
                logger.error("Failed to send even simplified notification")
                return False

    async def notify_position_closed_async(self, symbol, side, entry_price, exit_price, pnl, roe, reason=None):
        try:
            message = self._format_position_closed(symbol, side, entry_price, exit_price, pnl, roe, reason)
            return await self.send_message_async(message)
        except Exception as e:
            logger.error(f"Error formatting async position closed notification: {e}")
            simple_message = f"POSICAO FECHADA: {symbol} | PnL: {pnl if pnl else 0.0}"
            return await self.send_message_async(simple_message)

    def notify_bot_started(self):
        """Notify when bot starts"""
        return self.send_message(self._bot_started_message())

    async def notify_bot_started_async(self):
        return await self.send_message_async(self._bot_started_message())

    def notify_bot_stopped(self):
        """Notify when bot stops"""
        return self.send_message(self._bot_stopped_message())

    async def notify_bot_stopped_async(self):
        return await self.send_message_async(self._bot_stopped_message())

    async def notify_monitoring_async(self, note=None):
        return await self.send_message_async(self._bot_observing_message(note))


telegram_notifier = TelegramNotifier()
