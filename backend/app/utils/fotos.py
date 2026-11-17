import os
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, status

MAX_FOTO_SIZE_BYTES = 5 * 1024 * 1024  # 5MB máximo por foto
MAX_FOTOS_POR_CHAMADO = 10  # Máximo de fotos no chamado
EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}


def validar_conteudo_foto(arquivo_bytes: bytes, nome_arquivo: str) -> str:
    """
    Valida rigorosamente:
    1. Extensão declarada (apenas .jpg, .jpeg, .png, .webp).
    2. Tamanho em bytes (máximo 5MB).
    3. Magic bytes / assinatura real do arquivo para evitar que arquivos de texto, HTML,
       scripts PHP/JS ou executáveis sejam mascarados com extensão de imagem.
    Retorna a extensão canônica segura (ex: '.png', '.jpg', '.webp').
    """
    ext = Path(nome_arquivo).suffix.lower()
    if ext not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão '{ext}' não permitida. Envie apenas imagens JPG, PNG ou WEBP.",
        )

    if len(arquivo_bytes) > MAX_FOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo excede o tamanho máximo permitido de 5MB ({len(arquivo_bytes) / (1024*1024):.2f}MB enviados).",
        )

    if len(arquivo_bytes) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido ou corrompido (tamanho insuficiente para cabeçalho de imagem).",
        )

    # Magic Bytes (Assinaturas binárias reais)
    # JPEG: Inicia com FF D8 FF
    is_jpeg = arquivo_bytes.startswith(b"\xff\xd8\xff")
    # PNG: Inicia com 89 50 4E 47 0D 0A 1A 0A
    is_png = arquivo_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    # WEBP: Inicia com RIFF....WEBP
    is_webp = (
        arquivo_bytes.startswith(b"RIFF")
        and len(arquivo_bytes) >= 12
        and arquivo_bytes[8:12] == b"WEBP"
    )

    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conteúdo do arquivo não é uma imagem válida. Arquivos HTML, textos e scripts são proibidos.",
        )

    if is_png:
        return ".png"
    if is_jpeg:
        return ".jpg"
    return ".webp"
