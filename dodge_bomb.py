import os
import sys
import pygame as pg
import random

WIDTH, HEIGHT = 1100, 650
# 修正
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


def gameover(screen: pg.Surface, survival_time: float) -> None:
    # 半透明の黒いオーバーレイに「Game Over」と左右のこうかとん画像を表示する
    w, h = screen.get_size()
    overlay = pg.Surface((w, h), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # (R,G,B,alpha)

    # フォントとテキスト
    font = pg.font.Font(None, 80)
    text_surf = font.render("Game Over", True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(w // 2, h // 2))
    overlay.blit(text_surf, text_rect)

    time_surf = font.render(f"Time: {survival_time:.2f}s", True, (255, 255, 255))
    time_rect = time_surf.get_rect(topright=(w - 30, 30))
    overlay.blit(time_surf, time_rect)

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


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    時間とともに爆弾が拡大、加速するための爆弾Surfaceリストと加速度リストを返す
    戻り値：爆弾Surfaceのリスト、加速度のリスト
    """
    bb_imgs = []
    for r in range(1, 11):
        bb_img = pg.Surface((20 * r, 20 * r))
        pg.draw.circle(bb_img, (255, 0, 0), (10 * r, 10 * r), 10 * r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)
    # 加速度のリスト
    bb_accs = [a for a in range(1, 11)]
    return bb_imgs, bb_accs


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """
    飛ぶ方向に従ってこうかとん画像を切り替えるための辞書を返す
    キー：移動量タプル、値：rotozoomしたSurface
    """
    kk_dict = {}
    # 8方向の移動量に対応する回転角度と反転フラグを設定
    direction_config = {
        (0, 0): (0, False),  # キー押下なし
        (5, 0): (0, True),  # 右
        (5, -5): (45, True),  # 右上
        (0, -5): (90, True),  # 上
        (-5, -5): (-45, False),  # 左上
        (-5, 0): (0, False),  # 左
        (-5, 5): (45, False),  # 左下
        (0, 5): (-90, True),  # 下
        (5, 5): (-45, True),  # 右下
    }

    kk_base = pg.image.load("fig/3.png")

    for direction, (angle, flip_horizontal) in direction_config.items():
        kk_img = kk_base
        if flip_horizontal:
            kk_img = pg.transform.flip(kk_base, True, False)
        kk_dict[direction] = pg.transform.rotozoom(kk_img, angle, 0.9)

    return kk_dict


def calc_orientation(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    追従型爆弾の移動方向を計算する
    引数：org（爆弾のRect）、dst（こうかとんのRect）、current_xy（現在の速度ベクトル）
    戻り値：新しい速度ベクトル（vx, vy）
    """
    import math

    # 爆弾からこうかとんへのベクトルを計算
    dx = dst.centerx - org.centerx
    dy = dst.centery - org.centery

    # 距離を計算
    distance = math.sqrt(dx**2 + dy**2)

    # こうかとんが遠い場合のみ追従、近い場合は現在の方向を保持
    if distance >= 300:
        # ノルムが√50になるように正規化
        if distance > 0:
            norm = math.sqrt(50)
            vx = (dx / distance) * norm
            vy = (dy / distance) * norm
            return vx, vy

    # こうかとんが近い場合は現在の方向を保持
    return current_xy


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    font = pg.font.Font(None, 80)

    # こうかとんの初期化
    kk_imgs = get_kk_imgs()  # 演習課題3：方向に応じた画像辞書
    kk_img = kk_imgs[(0, 0)]  # 初期状態：キー押下なし
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 爆弾の初期化（演習課題2：時間とともに拡大、加速）
    bb_imgs, bb_accs = init_bb_imgs()
    vx, vy = +5, +5
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
    bb_img.set_colorkey((0, 0, 0))  # 透明化

    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        # ゲームオーバー時の処理
        if kk_rct.colliderect(bb_rct):
            print("ゲームオーバー")
            gameover(screen, tmr / 50)
            return

        screen.blit(bg_img, [0, 0])

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]

        # 押されているキーに応じて移動量を加算する
        for k, mv in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])

        # 演習課題3：移動方向に応じてこうかとん画像を切り替える
        sum_mv_tuple = tuple(sum_mv)
        if sum_mv_tuple in kk_imgs:
            kk_img = kk_imgs[sum_mv_tuple]

        screen.blit(kk_img, kk_rct)

        # 演習課題4：追従型爆弾で速度を更新
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))

        # 演習課題2：時間とともに爆弾が拡大、加速
        # tmrの値に応じて爆弾のサイズと速度を変更
        stage = min(tmr // 500, 9)  # 0～9段階
        bb_img = bb_imgs[stage]
        bb_img.set_colorkey((0, 0, 0))

        # 爆弾のRectを更新（サイズ変更に対応）
        old_center = bb_rct.center
        bb_rct = bb_img.get_rect()
        bb_rct.center = old_center

        # 加速度に応じた速度更新
        avx = vx * bb_accs[stage]
        avy = vy * bb_accs[stage]

        bb_rct.move_ip(avx, avy)
        yoko, tate = check_bound(bb_rct)
        # 更新後の座標が画面外になった場合の挙動
        # bb_rct：横（縦）方向に出そうになったらvx（vy）の符号を反転する
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1

        screen.blit(bb_img, bb_rct)

        # 生存時間を右上に表示
        survival_surf = font.render(f"Time: {tmr / 50:.2f}s", True, (255, 255, 255))
        survival_rect = survival_surf.get_rect(topright=(WIDTH - 20, 20))
        screen.blit(survival_surf, survival_rect)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
