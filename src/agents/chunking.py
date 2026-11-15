# src/agents/chunking.py

def chunk_text(text: str, max_chars: int = 3000, overlap: int = 200) -> list[str]:
    """
    将长文本切分为多个块。
    max_chars: 每个块的最大字符数
    overlap: 相邻块之间的重叠字符数，防止把一句完整的话切断
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        # 找到理论的结束位置
        end = start + max_chars
        
        # 如果不是最后一块，尝试在段落或句号处截断
        if end < len(text):
            # 从理论结束位置往回找换行符，避免把段落切碎
            cut = text.rfind('\n', start, end)
            if cut == -1 or cut < start + max_chars // 2:
                # 找不到合适的换行，就找句号
                cut = text.rfind('。', start, end)
            if cut == -1 or cut < start + max_chars // 2:
                # 实在找不到，只能硬切
                cut = end
            end = cut + 1 # 包含标点符号

        chunks.append(text[start:end].strip())
        
        # 下一个块的起点，减去重叠部分
        start = end - overlap
        if start < 0:
            start = 0
        # 防止死循环
        if end == len(text):
            break

    return chunks