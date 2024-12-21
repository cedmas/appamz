from datetime import datetime
import pytz

# Configuração do fuso horário de Recife
try:
    RECIFE_TZ = pytz.timezone('America/Recife')
except Exception as e:
    raise ValueError(f"Erro ao configurar o fuso horário: {e}")

def get_current_time():
    """
    Retorna o horário atual no fuso horário de Recife, formatado como string.
    
    Returns:
        str: Data e hora no formato 'YYYY-MM-DD HH:MM:SS'.
    """
    try:
        return datetime.now(RECIFE_TZ).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        raise ValueError(f"Erro ao obter o horário atual: {e}")
