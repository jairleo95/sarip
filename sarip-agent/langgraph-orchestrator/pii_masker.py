import re

def mask_pii(text: str) -> str:
    """
    Capa de PII Masking:
    Procesa cualquier texto libre y ofusca identificadores sensibles (Números de cuenta, emails, DNI/SSN).
    En MVP lo hacemos con RegEx rápidas antes de pasarle la cadena al Grafo de IA.
    """
    if not text:
        return text

    # 1. Enmascarar números de cuenta (ej. 13-4452-9999 -> XX-XXXX-9999)
    # Suponiendo un patrón común de cuenta bancaria o tarjeta
    account_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    
    def mask_account(match):
        digits = re.sub(r'[ -]', '', match.group(0))
        if len(digits) >= 4:
            return '*' * (len(digits) - 4) + digits[-4:]
        return '*' * len(digits)

    masked_text = re.sub(account_pattern, mask_account, text)
    
    # 2. Enmascarar correos electrónicos (ej. juan.perez@email.com -> j***z@email.com)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    masked_text = re.sub(email_pattern, "[EMAIL_REDACTED]", masked_text)
    
    # 3. Enmascarar DNI/IDs (ej. 72345678 -> 72****78)
    # Formato simple de 8 digitos
    dni_pattern = r'\b[0-9]{8}\b'
    masked_text = re.sub(dni_pattern, "[ID_REDACTED]", masked_text)

    return masked_text
