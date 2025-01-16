class InstagramBotError(Exception):
    """Clase base para excepciones del bot"""
    pass

class RateLimitError(InstagramBotError):
    """Error cuando se excede el límite de acciones"""
    pass

class AuthenticationError(InstagramBotError):
    """Error en la autenticación"""
    pass