# meta developer: @space_modules
# meta banner : https://files.catbox.moe/3gqrlz.jpg
# requires: requests

import random
import string
import requests
import uuid
import re
import html 
from .. import loader, utils
from telethon.tl.types import Message


def generate_random_string(length=10):
    """Generates a random string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@loader.tds
class TempMailMod(loader.Module):
    """Temporary email module"""
    
    strings = {
        "name": "TempMail",
        "processing": "✨ <b>Creating email...</b>",
        "loading_message": "🔄 <b>Loading message...</b>",
        "email_created": "📧 <b>Email created!</b>\n<code>{email}</code>\n\nClick <b>Refresh</b> to check for messages.",
        "no_messages": "📧 <code>{email}</code>\n\n📭 <b>No messages yet.</b>",
        "message_page_view": "📬 <b>Message {current_page} of {total_pages}</b> for <code>{email}</code>:\n\n{message}",
        "message_item": "<b>From:</b> <code>{sender}</code>\n<b>Subject:</b> <code>{subject}</code>\n\n<blockquote>{body}</blockquote>",
        "refresh_btn": "🔄 Refresh",
        "delete_btn": "🗑️ Delete",
        "prev_btn": "« Prev",
        "next_btn": "Next »",
        "page_indicator": "{current}/{total}",
        "error": "❌ <b>Error:</b> <code>{error}</code>",
        "deleted": "🗑 <b>Email account deleted!</b>",
        "email_not_found": "❓ <b>Email not found or deleted.</b>"
    }
    strings_ru = {
        "processing": "✨ <b>Создание email...</b>",
        "loading_message": "🔄 <b>Загрузка сообщения...</b>",
        "email_created": "📧 <b>Временный email создан!</b>\n<code>{email}</code>\n\nНажмите <b>Обновить</b> для проверки.",
        "no_messages": "📧 <code>{email}</code>\n\n📭 <b>Пока нет сообщений.</b>",
        "message_page_view": "📬 <b>Сообщение {current_page} из {total_pages}</b> для <code>{email}</code>:\n\n{message}",
        "message_item": "<b>От:</b> <code>{sender}</code>\n<b>Тема:</b> <code>{subject}</code>\n\n<blockquote>{body}</blockquote>",
        "refresh_btn": "🔄 Обновить",
        "delete_btn": "🗑️ Удалить",
        "prev_btn": "« Назад",
        "next_btn": "Вперёд »",
        "page_indicator": "{current}/{total}",
        "error": "❌ <b>Ошибка:</b> <code>{error}</code>",
        "deleted": "🗑 <b>Email-аккаунт удален!</b>",
        "email_not_found": "❓ <b>Email не найден или уже удален.</b>"
    }

    def __init__(self):
        self.api_base = "https://api.mail.tm"
        # Module by @gemeguardian

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.active_emails = self.db.get("TempMail", "active_emails", {})

    @loader.command(ru_doc="Создать временный email")
    async def tempmail(self, message: Message):
        """Create a temporary email"""
        msg = await utils.answer(message, self.strings("processing"))
        
        try:
            domains_res = await utils.run_sync(requests.get, f"{self.api_base}/domains")
            domains_res.raise_for_status()
            domain = domains_res.json()['hydra:member'][0]['domain']
            
            address = f"{generate_random_string(15)}@{domain}"
            password = generate_random_string(20)
            
            account_res = await utils.run_sync(requests.post, f"{self.api_base}/accounts", json={"address": address, "password": password})
            account_res.raise_for_status()
            
            token_res = await utils.run_sync(requests.post, f"{self.api_base}/token", json={"address": address, "password": password})
            token_res.raise_for_status()
            
            session_id = str(uuid.uuid4())
            self.active_emails[session_id] = {
                "address": address,
                "account_id": account_res.json()['id'],
                "token": token_res.json()['token']
            }
            self.db.set("TempMail", "active_emails", self.active_emails)
            
            await self.inline.form(
                message=msg,
                text=self.strings("email_created").format(email=address),
                reply_markup=[[{
                    "text": self.strings("refresh_btn"), 
                    "callback": self.update_messages, 
                    "args": (session_id, 0)
                }, {
                    "text": self.strings("delete_btn"), 
                    "callback": self.delete_email, 
                    "args": (session_id,)
                }]]
            )

        except Exception as e:
            error = f"{e.response.status_code}\n{e.response.text}" if hasattr(e, 'response') else str(e)
            await utils.answer(msg, self.strings("error").format(error=error))

    async def update_messages(self, call, session_id: str, page: int = 0):
        if not (session_data := self.active_emails.get(session_id)):
            await call.answer("Email session not found!", show_alert=True)
            return await call.edit(self.strings("email_not_found"))
        
        try:
            await call.edit(self.strings("loading_message"))
        except Exception:
            pass

        try:
            headers = {'Authorization': f'Bearer {session_data["token"]}'}
            messages_res = await utils.run_sync(requests.get, f"{self.api_base}/messages", headers=headers, timeout=15)
            messages_res.raise_for_status()
            messages = messages_res.json()['hydra:member']
            email_address = session_data.get("address", "...")
            
            if not messages:
                return await call.edit(
                    text=self.strings("no_messages").format(email=email_address),
                    reply_markup=[[{
                        "text": self.strings("refresh_btn"),
                        "callback": self.update_messages,
                        "args": (session_id, 0)
                    }, {
                        "text": self.strings("delete_btn"),
                        "callback": self.delete_email,
                        "args": (session_id,)
                    }]]
                )
            
            total_pages = len(messages)
            page = max(0, min(page, total_pages - 1))
            
            message_id = messages[page]['id']
            full_message_res = await utils.run_sync(requests.get, f"{self.api_base}/messages/{message_id}", headers=headers, timeout=15)
            full_message_res.raise_for_status()
            full_message_data = full_message_res.json()

            nav_row = []
            if page > 0:
                nav_row.append({"text": self.strings("prev_btn"), "callback": self.update_messages, "args": (session_id, page - 1)})
            nav_row.append({"text": self.strings("page_indicator").format(current=page + 1, total=total_pages), "callback": "empty"})
            if page < total_pages - 1:
                nav_row.append({"text": self.strings("next_btn"), "callback": self.update_messages, "args": (session_id, page + 1)})

            control_row = [
                {"text": self.strings("refresh_btn"), "callback": self.update_messages, "args": (session_id, page)},
                {"text": self.strings("delete_btn"), "callback": self.delete_email, "args": (session_id,)}
            ]
            
            try:
                body_content = ""
                raw_body = ""
                is_html = False
                html_body = full_message_data.get('html')
               
                if html_body and isinstance(html_body, list) and html_body:
                    raw_body = "".join(html_body)
                    raw_body = html.unescape(raw_body)
                    is_html = True
                else:
                    raw_body = full_message_data.get('text', 'Could not load full message.')
                    raw_body = html.unescape(raw_body) 

                if len(raw_body) > 3500:
                    plain_text = re.sub(r'<[^>]+>', '', raw_body)
                    truncated_text = plain_text[:3500] + "\n\n[Message truncated]"
                    body_content = utils.escape_html(truncated_text)
                else:
                    if is_html:
                        body_content = raw_body
                        replacements = { r'<br\s*/?>': '\n', r'<strong\b[^>]*>': '<b>', r'</strong>': '</b>', r'<em\b[^>]*>': '<i>', r'</i>': '</i>' }
                        for p, r in replacements.items(): body_content = re.sub(p, r, body_content, flags=re.IGNORECASE)
                        allowed_tags = r'a|b|i|u|s|code|pre|blockquote'
                        body_content = re.sub(r'</?(?!(' + allowed_tags + r')\b)[^>]*?>', '', body_content, flags=re.IGNORECASE)
                    else:
                        body_content = utils.escape_html(raw_body)
                
                message_item_text = self.strings("message_item").format(sender=full_message_data.get("from", {}).get("address", "Unknown"), subject=full_message_data.get("subject", "No Subject"), body=body_content)
                full_text = self.strings("message_page_view").format(current_page=page + 1, total_pages=total_pages, email=email_address, message=message_item_text)
                
                await call.edit(full_text, reply_markup=[nav_row, control_row])

            except Exception as e:
                if "can't parse entities" in str(e):
                    plain_body = full_message_data.get('text', 'Could not load full message.')
                    plain_body = html.unescape(plain_body)  
                    if len(plain_body) > 3500:
                        plain_body = plain_body[:3500] + "\n\n[Message truncated]"
                    
                    body_content = utils.escape_html(plain_body)
                    message_item_text = self.strings("message_item").format(sender=full_message_data.get("from", {}).get("address", "Unknown"), subject=full_message_data.get("subject", "No Subject"), body=body_content)
                    full_text = self.strings("message_page_view").format(current_page=page + 1, total_pages=total_pages, email=email_address, message=message_item_text)
                    await call.edit(full_text, reply_markup=[nav_row, control_row])
                else:
                    raise e
            
        except Exception as e:
            error = f"{e.response.status_code}\n{e.response.text}" if hasattr(e, 'response') else str(e)
            await call.answer(f"Error: {error}", show_alert=True)

    async def delete_email(self, call, session_id: str):
        if not (session_data := self.active_emails.get(session_id)):
            await call.answer("Email session not found!", show_alert=True)
            return await call.edit(self.strings("email_not_found"))

        try:
            headers = {'Authorization': f'Bearer {session_data["token"]}'}
            delete_res = await utils.run_sync(requests.delete, f"{self.api_base}/accounts/{session_data['account_id']}", headers=headers, timeout=15)
            delete_res.raise_for_status()
            
            del self.active_emails[session_id]
            self.db.set("TempMail", "active_emails", self.active_emails)
            await call.edit(self.strings("deleted"))

        except Exception as e:
            error = f"{e.response.status_code}\n{e.response.text}" if hasattr(e, 'response') else str(e)
            await call.answer(f"Failed to delete: {error}", show_alert=True)
