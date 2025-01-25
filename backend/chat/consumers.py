from datetime import timezone
import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import ChatMessage
from core.models.user import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection with JWT authentication"""
        try:
            await self._authenticate_user()
            await self._validate_user()
            await self._add_to_chat_group()
            await self.accept()
        except (InvalidToken, PermissionError) as e:
            await self.close(code=4001)
        except Exception as e:
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            payload = await self._validate_message(text_data)
            await self._save_message(payload['message'])
            await self._broadcast_message(payload)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
        except KeyError:
            await self._send_error("Missing required fields")
        except ValueError as e:
            await self._send_error(str(e))

    async def chat_message(self, event):
        """Send message to WebSocket client"""
        await self.send(text_data=json.dumps(event['payload']))

    # Helper methods
    async def _authenticate_user(self):
        """Extract and validate JWT token from query parameters"""
        query_params = parse_qs(self.scope["query_string"].decode())
        token = query_params.get('token', [None])[0]
        
        if not token:
            raise PermissionError("Missing authentication token")
            
        self.user = await self._get_user_from_token(token)
        
        if isinstance(self.user, AnonymousUser):
            raise InvalidToken("Invalid authentication token")

    async def _validate_user(self):
        """Ensure user has permission to chat"""
        if not self.user.is_active:
            raise PermissionError("User account is disabled")
            
        if self.user.role == 'dorm_owner' and not self.user.is_verified:
            raise PermissionError("Unverified dorm owner")

    async def _add_to_chat_group(self):
        """Add user to appropriate chat group"""
        self.room_group_name = f"chat_{self.user.dorm.id}"  # Assuming user has dorm relation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    async def _validate_message(self, text_data):
        """Validate and parse incoming message"""
        payload = json.loads(text_data)
        
        if len(payload.get('message', '')) > 500:
            raise ValueError("Message too long (max 500 characters)")
            
        if not payload.get('message'):
            raise ValueError("Empty messages are not allowed")
            
        return payload

    async def _broadcast_message(self, payload):
        """Send message to chat group"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'payload': {
                    'sender': self.user.username,
                    'message': payload['message'],
                    'timestamp': str(timezone.now()),
                }
            }
        )

    async def _send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    @database_sync_to_async
    def _get_user_from_token(self, token):
        """Retrieve user from JWT token"""
        try:
            access_token = AccessToken(token)
            return User.objects.get(id=access_token['user_id'])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()

    @database_sync_to_async
    def _save_message(self, message):
        """Persist message to database"""
        ChatMessage.objects.create(
            sender=self.user,
            message=message,
            dorm=self.user.dorm,  # Assuming user has dorm relation
            # Add receiver logic based on your requirements
        )