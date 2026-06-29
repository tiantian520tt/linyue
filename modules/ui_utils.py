import pygame

def render_text_wrapped(surface, text, font, color, rect):
    """完美复刻原有的文本自动换行渲染逻辑"""
    if not text: 
        return
    x, y = rect.topleft
    line_height = font.get_linesize()
    
    max_chars = 45 
    paragraphs = text.split('\n')
    for para in paragraphs:
        for i in range(0, len(para), max_chars):
            chunk = para[i:i + max_chars]
            surf = font.render(chunk, True, color)
            surface.blit(surf, (x, y))
            y += line_height
            if y > rect.bottom: 
                break