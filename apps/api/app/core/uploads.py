from fastapi import HTTPException, UploadFile


async def read_text_upload(file: UploadFile, *, max_bytes: int) -> str:
    """Read an uploaded text file with a hard byte limit."""
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds maximum size of {max_bytes // 1024} KB",
            )
        chunks.append(chunk)

    try:
        return b"".join(chunks).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Upload must be valid UTF-8 text") from exc
