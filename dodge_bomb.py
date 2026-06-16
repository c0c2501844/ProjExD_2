import os
import sys
import pygame as pg
import random

WIDTH, HEIGHT = 1100, 650
DELTA = {pg.K_UP: (0, -5), pg.K_DOWN: (0, +5), pg.K_LEFT: (-5, 0), pg.K_RIGHT: (+5, 0)}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    # 引数：こうかとんRect or 爆弾Rect
    # 戻り値：横方向、縦方向の真理値タプル（画面内：True／画面外：False）
    # Rectオブジェクトのleft, right, top, bottomの値から画面内・外を判断する
    yoko, tate = True, True
    if rct.left < 0 or WIDTH < rct.right:
        yoko = False
    if rct.top < 0 or HEIGHT < rct.bottom:
        tate = False
    return yoko, tate


def gameover(screen: pg.Surface) -> None:
    # 半透明の黒いオーバーレイに「Game Over」と左右のこうかとん画像を表示する
    w, h = screen.get_size()
    overlay = pg.Surface((w, h), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # (R,G,B,alpha)

    # フォントとテキスト
    font = pg.font.Font(None, 80)
    text_surf = font.render("Game Over", True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(w // 2, h // 2))
    overlay.blit(text_surf, text_rect)

    # 両端のこうかとん画像を読み込んで配置
    try:
        kk_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    except Exception:
        kk_img = None

    if kk_img:
        left_img = kk_img
        right_img = kk_img
        lrect = left_img.get_rect()
        rrect = right_img.get_rect()
        # テキストの左右に並べる
        lrect.center = (text_rect.left - lrect.width // 2 - 20, h // 2)
        rrect.center = (text_rect.right + rrect.width // 2 + 20, h // 2)
        overlay.blit(left_img, lrect)
        overlay.blit(right_img, rrect)

    screen.blit(overlay, (0, 0))
    pg.display.update()
    pg.time.delay(5000)


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    font = pg.font.Font(None, 80)

    # こうかとんの初期化
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 爆弾の初期化
    vx, vy = +5, +5
    bom_width, bom_height = 200, 200
    bb_img = pg.Surface((bom_width, bom_height))
    pg.draw.circle(bb_img, (255, 0, 0), (bom_width // 2, bom_height // 2), bom_width // 2)
    bb_img.set_colorkey((0, 0, 0))
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

            # ゲームオーバー時の処理
            if kk_rct.colliderect(bb_rct):
                print("ゲームオーバー")
                gameover(screen)
                pg.time.delay(2000)
                return

        screen.blit(bg_img, [0, 0])

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]

        for k, mv in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])
        screen.blit(kk_img, kk_rct)

        bb_rct.move_ip(vx, vy)
        yoko, tate = check_bound(bb_rct)
        # 更新後の座標が画面外になった場合の挙動
        # kk_rct：更新前の位置に戻す
        # bb_rct：横（縦）方向に出そうになったらvx（vy）の符号を反転する
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1
        screen.blit(bb_img, bb_rct)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
