# -*- coding: utf-8 -*-
"""
这里是专门用来画画的搬砖模块。
主线程太高贵了，不应该塞满各种矩形和文字渲染。
"""
import pygame
import math
import os
import random
from modules.ui_utils import render_text_wrapped

def ease_out_elastic(x):
    """别问，问就是高大上的数学弹性动效公式"""
    if x <= 0: return 0
    if x >= 1: return 1
    c4 = (2 * math.pi) / 3
    return math.pow(2, -10 * x) * math.sin((x * 10 - 0.75) * c4) + 1

def draw_notifications(engine):
    """左上角的好感度提示，带弹簧动画的那种"""
    active_notifs = []
    for i, notif in enumerate(engine.notifications):
        dt = pygame.time.get_ticks() - notif["timer"]
        if dt > 6000: continue 
        
        active_notifs.append(notif)
        p = min(1.0, dt / 800.0) 
        target_y = 80 + i * 45
        current_y = target_y - 80 * (1 - ease_out_elastic(p)) 
        
        alpha = 255
        if dt > 5000: alpha = int(255 * (6000 - dt) / 1000.0) 
            
        notif_surf = engine.sys_font.render(notif["text"], True, notif["color"])
        bg_rect = pygame.Rect(30, int(current_y), notif_surf.get_width() + 40, 35)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        
        pygame.draw.rect(bg_surf, (20, 24, 35, int(alpha * 0.85)), bg_surf.get_rect(), border_radius=18)
        pygame.draw.rect(bg_surf, (*notif["color"], int(alpha * 0.6)), bg_surf.get_rect(), width=1, border_radius=18)
        
        engine.screen.blit(bg_surf, bg_rect)
        notif_surf.set_alpha(alpha)
        engine.screen.blit(notif_surf, (50, int(current_y) + 8))
        
    engine.notifications = active_notifs

def draw_history_panel(engine):
    """回忆录面板。点开就能看到以前被大模型调戏的历史记录"""
    if not getattr(engine, 'show_history_ui', False): return
    
    t = pygame.time.get_ticks() - engine.history_open_time
    p = min(1.0, t / 600.0)
    y_offset = -engine.HEIGHT * (1 - ease_out_elastic(p))
    
    overlay = pygame.Surface((engine.WIDTH, engine.HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 12, 18, 245))
    
    title = engine.splash_font.render("回 忆 录", True, (235, 213, 140))
    overlay.blit(title, (50, 40))
    sub = engine.sys_font.render("滚动鼠标滚轮查看历史 | 按 [ESC] 或点击右上角关闭", True, (150, 150, 150))
    overlay.blit(sub, (50, 120))
    
    engine.close_btn_rect = pygame.Rect(engine.WIDTH - 90, 40, 40, 40)
    is_hover = engine.close_btn_rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(overlay, (255, 100, 100, 220 if is_hover else 150), engine.close_btn_rect, border_radius=10)
    x_txt = engine.name_font.render("X", True, (255, 255, 255))
    overlay.blit(x_txt, x_txt.get_rect(center=engine.close_btn_rect.center))
    
    start_y = 180 + engine.history_scroll_y
    for i, rec in enumerate(reversed(engine.backend.rich_history)):
        card_y = start_y + i * 160
        if card_y > engine.HEIGHT or card_y < 20: continue 
        
        card_rect = pygame.Rect(50, card_y, engine.WIDTH - 100, 140)
        pygame.draw.rect(overlay, (30, 35, 45, 200), card_rect, border_radius=15)
        pygame.draw.rect(overlay, (255, 255, 255, 30), card_rect, width=1, border_radius=15)
        
        img_path = rec.get("image", "")
        if img_path not in engine.history_img_cache:
            if os.path.exists(img_path):
                try:
                    thumb = pygame.image.load(img_path)
                    thumb = pygame.transform.smoothscale(thumb, (213, 120)) 
                    engine.history_img_cache[img_path] = thumb
                except: engine.history_img_cache[img_path] = None
            else: engine.history_img_cache[img_path] = None
        
        thumb = engine.history_img_cache[img_path]
        if thumb:
            overlay.blit(thumb, (60, card_y + 10))
        
        time_cn = {"morning":"清晨", "noon":"正午", "afternoon":"午后", "evening":"傍晚", "night":"深夜"}.get(rec.get('time','').lower(), rec.get('time',''))
        info_txt = f"第 {rec.get('day', 1)} 天 | {time_cn} | 状态: {rec.get('activity', '无')} | 心情: {rec.get('mood', 50)}"
        info_surf = engine.hud_font.render(info_txt, True, (235, 213, 140))
        overlay.blit(info_surf, (290, card_y + 15))
        
        render_text_wrapped(overlay, rec.get("text", ""), engine.font, (230, 230, 230), pygame.Rect(290, card_y + 45, engine.WIDTH - 420, 80))
    
    max_scroll = max(0, len(engine.backend.rich_history) * 160 - (engine.HEIGHT - 200))
    if engine.history_scroll_y < -max_scroll: engine.history_scroll_y = -max_scroll
    
    engine.screen.blit(overlay, (0, int(y_offset)))

def draw_modern_dialogue_box(engine):
    """炫酷二次元风格对话框"""
    box_rect = pygame.Rect(80, 500, 1120, 180)
    bg_surf = pygame.Surface((box_rect.w, box_rect.h), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (20, 24, 35, 210), bg_surf.get_rect(), border_radius=15)
    pygame.draw.rect(bg_surf, (255, 255, 255, 40), bg_surf.get_rect(), width=1, border_radius=15)
    engine.screen.blit(bg_surf, box_rect)

    name_surf = engine.name_font.render(engine.char_name, True, (235, 213, 140)) 
    name_width = max(140, name_surf.get_width() + 60) 

    name_bg = pygame.Surface((name_width, 40), pygame.SRCALPHA)
    pygame.draw.rect(name_bg, (40, 45, 60, 240), name_bg.get_rect(), border_radius=20)
    pygame.draw.rect(name_bg, (235, 213, 140, 150), name_bg.get_rect(), width=2, border_radius=20)
    engine.screen.blit(name_bg, (100, 480))
    
    name_rect = name_surf.get_rect(center=(100 + name_width // 2, 500))
    engine.screen.blit(name_surf, name_rect)

    render_text_wrapped(engine.screen, engine.current_text, engine.font, (245, 245, 245), pygame.Rect(120, 540, 1040, 120))
    
    sys_txt = "LinYue AI Engine" if not engine.is_thinking and not engine.status_msg else f"Sys: {engine.status_msg}"
    status_surf = engine.sys_font.render(sys_txt, True, (150, 150, 160))
    status_rect = status_surf.get_rect()
    status_rect.bottomright = (box_rect.right - 20, box_rect.bottom - 15) 
    engine.screen.blit(status_surf, status_rect)

    copy_surf = engine.sys_font.render("LinYue AIChat by r1kk3", True, (100, 100, 100))
    engine.screen.blit(copy_surf, (15, engine.HEIGHT - 30))

def draw_top_hud(engine):
    """顶部状态栏：记录存活天数、当前时间和背景音乐开关"""
    time_cn_map = {"morning":"清晨", "noon":"正午", "afternoon":"午后", "evening":"傍晚", "night":"深夜"}
    t_cn = time_cn_map.get(engine.current_time.lower(), engine.current_time)
    
    hud_text = f"第 {engine.backend.day_count} 天 {t_cn} | {engine.current_activity if engine.current_activity else '闲聊中'}"
    hud_surf = engine.hud_font.render(hud_text, True, (230, 230, 230))
    hud_width = max(300, hud_surf.get_width() + 70)
    
    hud_bg = pygame.Surface((hud_width, 45), pygame.SRCALPHA)
    pygame.draw.rect(hud_bg, (20, 24, 35, 180), hud_bg.get_rect(), border_radius=22)
    pygame.draw.rect(hud_bg, (255, 255, 255, 30), hud_bg.get_rect(), width=1, border_radius=22)
    engine.screen.blit(hud_bg, (30, 20))
    
    pygame.draw.circle(engine.screen, (235, 213, 140), (55, 42), 6)
    engine.screen.blit(hud_surf, (75, 32))

    engine.music_btn_rect = pygame.Rect(1030, 20, 100, 45)
    is_m_hover = engine.music_btn_rect.collidepoint(pygame.mouse.get_pos())
    m_bg = pygame.Surface((100, 45), pygame.SRCALPHA)
    if engine.audio.music_enabled:
        pygame.draw.rect(m_bg, (255, 255, 255, 60) if is_m_hover else (255, 255, 255, 20), m_bg.get_rect(), border_radius=22)
        pygame.draw.rect(m_bg, (255, 255, 255, 100), m_bg.get_rect(), width=1, border_radius=22)
        m_txt = engine.hud_font.render("BGM: ON", True, (255, 255, 255))
    else:
        pygame.draw.rect(m_bg, (255, 100, 100, 60) if is_m_hover else (255, 100, 100, 20), m_bg.get_rect(), border_radius=22)
        pygame.draw.rect(m_bg, (255, 100, 100, 100), m_bg.get_rect(), width=1, border_radius=22)
        m_txt = engine.hud_font.render("BGM: OFF", True, (255, 180, 180))
    engine.screen.blit(m_bg, engine.music_btn_rect)
    engine.screen.blit(m_txt, m_txt.get_rect(center=engine.music_btn_rect.center))

    engine.history_btn_rect = pygame.Rect(1140, 20, 110, 45)
    is_h_hover = engine.history_btn_rect.collidepoint(pygame.mouse.get_pos())
    h_bg = pygame.Surface((110, 45), pygame.SRCALPHA)
    pygame.draw.rect(h_bg, (235, 213, 140, 60) if is_h_hover else (40, 45, 60, 200), h_bg.get_rect(), border_radius=22)
    pygame.draw.rect(h_bg, (235, 213, 140, 150), h_bg.get_rect(), width=1, border_radius=22)
    engine.screen.blit(h_bg, engine.history_btn_rect)
    h_txt = engine.hud_font.render("☰ 历史", True, (235, 213, 140) if not is_h_hover else (255,255,255))
    engine.screen.blit(h_txt, h_txt.get_rect(center=engine.history_btn_rect.center))

def draw_sleek_mood_bar(engine):
    """右侧微妙的心情指示器"""
    bar_x, bar_y, bar_w, bar_h = 1250, 200, 4, 300
    
    label_surf = engine.sys_font.render("心情", True, (200, 200, 200))
    label_rect = label_surf.get_rect(center=(bar_x + 2, bar_y - 20))
    engine.screen.blit(label_surf, label_rect)

    pygame.draw.rect(engine.screen, (255, 255, 255, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
    
    fill_h = int((engine.mood_value / 100) * bar_h)
    fill_y = bar_y + (bar_h - fill_h)
    
    r = int(255 * (100 - engine.mood_value) / 100)
    g = int(255 * engine.mood_value / 100)
    color = (r, g, 150)
    
    pygame.draw.rect(engine.screen, color, (bar_x, fill_y, bar_w, fill_h), border_radius=2)
    pygame.draw.circle(engine.screen, color, (bar_x + 2, fill_y), 8)
    pygame.draw.circle(engine.screen, (255, 255, 255), (bar_x + 2, fill_y), 4)

def draw_skip_button(engine):
    """让时光飞逝的剧情推进按钮"""
    if engine.current_activity and engine.state == 0: # 0对应 GameState.IDLE
        engine.skip_btn_rect = pygame.Rect(engine.WIDTH//2 - 75, 80, 150, 40)
        is_hover = engine.skip_btn_rect.collidepoint(pygame.mouse.get_pos())
        
        btn_bg = pygame.Surface((150, 40), pygame.SRCALPHA)
        fill_col = (235, 213, 140, 180) if is_hover else (40, 45, 60, 180)
        txt_col = (40, 40, 40) if is_hover else (235, 213, 140)
        
        pygame.draw.rect(btn_bg, fill_col, btn_bg.get_rect(), border_radius=20)
        pygame.draw.rect(btn_bg, (235, 213, 140, 100), btn_bg.get_rect(), width=1, border_radius=20)
        engine.screen.blit(btn_bg, engine.skip_btn_rect)
        
        skip_txt = engine.hud_font.render(">> 推进剧情", True, txt_col)
        engine.screen.blit(skip_txt, skip_txt.get_rect(center=engine.skip_btn_rect.center))
    else:
        engine.skip_btn_rect = None

def draw_input_panel(engine):
    """底部的打字输入框"""
    if engine.is_inputting:
        input_panel = pygame.Surface((1120, 60), pygame.SRCALPHA)
        input_panel.fill((20, 24, 35, 240))
        engine.screen.blit(input_panel, (80, 420))
        
        pygame.draw.rect(engine.screen, (235, 213, 140), pygame.Rect(80, 420, 1120, 60), width=2, border_radius=10)
        
        cursor = "_" if pygame.time.get_ticks() % 1000 < 500 else ""
        input_txt = engine.font.render(f"回复{engine.char_name}: {engine.user_input_buffer}{cursor}", True, (255, 255, 255))
        engine.screen.blit(input_txt, (100, 435))
    else:
        hint_txt = engine.sys_font.render("Press [ENTER] to reply / 按下回车键回复", True, (255, 255, 255, 150))
        engine.screen.blit(hint_txt, (100, 450))