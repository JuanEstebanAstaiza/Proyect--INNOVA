import jwt
import uuid
from datetime import datetime, timedelta
from flask import current_app
from typing import Dict, Optional

class JWTUtils:
    """Utilidades para manejo de tokens JWT en el sistema de sesiones"""

    @staticmethod
    def generate_session_token(user_id: int, session_id: str, device_info: Dict = None) -> str:
        """
        Genera un token JWT único para una sesión de usuario

        Args:
            user_id: ID del usuario
            session_id: ID único de la sesión
            device_info: Información del dispositivo (opcional)

        Returns:
            str: Token JWT generado
        """
        payload = {
            'user_id': user_id,
            'session_id': session_id,
            'device_fingerprint': str(uuid.uuid4()),  # Fingerprint único por sesión
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(
                minutes=current_app.config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']
            ),
            'type': 'session'
        }

        # Agregar información del dispositivo si está disponible
        if device_info:
            payload['device_info'] = {
                'user_agent': device_info.get('user_agent', ''),
                'platform': device_info.get('platform', ''),
                'language': device_info.get('language', ''),
                'timezone': device_info.get('timezone', ''),
                'screen_resolution': device_info.get('screen_resolution', ''),
                'cookie_enabled': device_info.get('cookie_enabled', True)
            }

        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )

        return token

    @staticmethod
    def validate_session_token(token: str) -> Optional[Dict]:
        """
        Valida un token JWT de sesión

        Args:
            token: Token JWT a validar

        Returns:
            Dict: Payload del token si es válido, None si no lo es
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )

            # Verificar que sea un token de sesión
            if payload.get('type') != 'session':
                return None

            # Verificar que no haya expirado
            exp_timestamp = payload.get('exp')
            if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            # Token expirado
            return None
        except jwt.InvalidTokenError:
            # Token inválido
            return None
        except Exception:
            # Error general
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """
        Decodifica un token JWT sin validar (útil para debugging)

        Args:
            token: Token JWT a decodificar

        Returns:
            Dict: Payload del token sin validar
        """
        try:
            # Decodificar sin verificar firma (solo para debugging)
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception:
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Verifica si un token JWT ha expirado

        Args:
            token: Token JWT a verificar

        Returns:
            bool: True si el token ha expirado
        """
        payload = JWTUtils.decode_token(token)
        if not payload:
            return True

        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return False

        return datetime.utcnow().timestamp() > exp_timestamp

    @staticmethod
    def get_token_info(token: str) -> Dict:
        """
        Obtiene información detallada de un token JWT

        Args:
            token: Token JWT a analizar

        Returns:
            Dict: Información completa del token
        """
        info = {
            'valid': False,
            'expired': True,
            'payload': None,
            'user_id': None,
            'session_id': None,
            'device_fingerprint': None,
            'issued_at': None,
            'expires_at': None,
            'device_info': None
        }

        payload = JWTUtils.decode_token(token)
        if payload:
            info['payload'] = payload
            info['user_id'] = payload.get('user_id')
            info['session_id'] = payload.get('session_id')
            info['device_fingerprint'] = payload.get('device_fingerprint')
            info['device_info'] = payload.get('device_info')

            # Convertir timestamps
            iat = payload.get('iat')
            exp = payload.get('exp')

            if iat:
                info['issued_at'] = datetime.fromtimestamp(iat)
            if exp:
                info['expires_at'] = datetime.fromtimestamp(exp)
                info['expired'] = datetime.utcnow().timestamp() > exp

            # Validar el token
            validation_payload = JWTUtils.validate_session_token(token)
            info['valid'] = validation_payload is not None

        return info

    @staticmethod
    def generate_device_fingerprint(device_info: Dict) -> str:
        """
        Genera un fingerprint único basado en información del dispositivo

        Args:
            device_info: Información del dispositivo

        Returns:
            str: Fingerprint único del dispositivo
        """
        # Crear un string único basado en características del dispositivo
        fingerprint_data = [
            device_info.get('user_agent', ''),
            device_info.get('platform', ''),
            device_info.get('language', ''),
            device_info.get('timezone', ''),
            device_info.get('screen_resolution', ''),
            str(device_info.get('cookie_enabled', True))
        ]

        # Crear un hash simple del fingerprint
        fingerprint_string = '|'.join(fingerprint_data)
        return str(hash(fingerprint_string))
