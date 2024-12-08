import pyxel
import random


class Map:
    OFS_X = 4  # マップ描画開始座標(X)
    OFS_Y = 10  # マップ描画開始座標(Y)
    SIZE = 16  # 1つのマップチップのサイズ

    @classmethod
    def to_screen(cls, x, y):
        px = cls.OFS_X + (cls.SIZE * x)
        py = cls.OFS_Y + (cls.SIZE * y)
        return px, py


class APP:
    OPENING = -1  # オープニング
    MAIN = 0  # メイン
    GAMECLEAR = 1  # ゲームクリア # 今回は使わない
    GAMEOVER = 2  # ゲームオーバー

    def __init__(self):
        pyxel.init(128, 128, title="pyxel", fps=30)
        pyxel.load("cat.pyxres")

        # self.cats = [] #バグ回避のために初期化

        self.init()

        pyxel.run(self.update, self.draw)

    def init(self):
        # OP用
        self.title_x = 25
        self.title_y = 50
        self.title_positions = [
            (self.title_x + i * 8, self.title_y) for i in range(len("STRAY STEPS"))
        ]

        self.current_stage = 0  # 現在のステージインデックス
        self.time_limit = 10  # 各ステージの制限時間（秒）
        self.start_time = pyxel.frame_count  # ステージ開始時のフレーム数を記録
        self.score = 0  # スコアを初期化

        self.state = self.OPENING  # 初期状態をオープニングに設定
        self.animation_frame = 0  # アニメーション用のフレームカウンタ

        # fontの読み込み
        self.umplus10 = pyxel.Font("umplus_j10r.bdf")
        # self.umplus12 = pyxel.Font("example/pyxel_examples/assets/umplus_j12r.bdf")

        # ED用
        self.cats = []

        # ステージ初期化
        self.stage_init()

    def get_map(self, x, y):  # ゲームオーバー判定用
        return self.map[y][x]

    # ステージの初期化
    def stage_init(self):
        # mapは、0:通行可能、1:障害物、2:通行済み

        self.map, self.x, self.y = (
            self.generate_valid_stage()
        )  # 一筆書き可能なステージを生成
        self.map_width = len(self.map[0])
        self.map_height = len(self.map)

        self.start_time = pyxel.frame_count  # ステージ開始時のフレーム数を記録

        # プレイヤーの初期位置
        self.map[self.y][self.x] = 2

    def generate_valid_stage(self):
        while True:
            stage = self.generate_random_stage()
            is_one_stroke_possible, start_x, start_y = self.is_one_stroke_possible(
                stage
            )
            if is_one_stroke_possible:
                return stage, start_x, start_y

    def generate_random_stage(self):
        # self.current_stageによって、ステージの難易度を変更
        size_base = (self.current_stage + 1) // 3 + 3
        width = random.randint(size_base, size_base + 3)  # ランダムな幅
        height = random.randint(size_base, size_base + 3)

        # 画面をはみ出すので最大値を7に設定
        width = min(width, 7)
        height = min(height, 7)

        # width = random.randint(3, 7)  # ランダムな幅
        # height = random.randint(3, 7)  # ランダムな高さ
        stage = [[0 for _ in range(width)] for _ in range(height)]
        # 1次元目がx, 2次元目がy,widthがx,heightがy

        # ランダムに障害物を配置
        # num_obstacles = random.randint(2, width * height // 3)
        num_obstacles = random.randint(self.current_stage // 2 + 2, width * height // 3)
        num_obstacles = random.randint(min(width, height) - 1, width * height // 3)
        # num_obstacles = 15
        coordinates = [(x, y) for x in range(width) for y in range(height)]
        random.shuffle(coordinates)
        obstacles = set(coordinates[:num_obstacles])
        # print(obstacles)

        for x, y in obstacles:
            stage[y][x] = 1  # 障害物を配置

        return stage

    def is_one_stroke_possible(self, stage):
        width = len(stage[0])
        height = len(stage)

        # 深さ優先探索、のちの判定のために深さを返す
        def dfs(x, y, visited, depth):
            if x < 0 or x >= width or y < 0 or y >= height:
                return depth - 1
            # 訪問済み、または、障害物の場合は、深さを返す
            if visited[y][x] or stage[y][x] == 1:
                return depth - 1
            visited[y][x] = True
            max_depth = depth
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                max_depth = max(max_depth, dfs(x + dx, y + dy, visited, depth + 1))
                # print(x + dx, y + dy, depth + 1, max_depth)
            return max_depth

        # dfs探索のスタート地点を探す
        start_x, start_y = None, None
        # スタート位置の偏りを無くしたいので、ランダムにスタート位置を選択
        coordinates = [(x, y) for y in range(height) for x in range(width)]
        # print(coordinates)
        random.shuffle(coordinates)
        for x, y in coordinates:
            if stage[y][x] == 0:  # 通行可能マスの場合
                start_x, start_y = x, y
                break
        if start_x is None:
            return False, None, None

        # 連結成分を確認
        visited = [[False for _ in range(width)] for _ in range(height)]
        max_depth = dfs(start_x, start_y, visited, 0)

        valid_point_num = 0
        for y in range(height):
            for x in range(width):
                if stage[y][x] == 0:
                    valid_point_num += 1
        if max_depth != valid_point_num - 1:
            return False, None, None
        else:
            return True, start_x, start_y

    def update(self):
        # アニメーションフレームの更新
        self.animation_frame = (self.animation_frame + 1) % 30  # 30フレームでループ

        # オープニング
        if self.state == self.OPENING:
            if pyxel.btnp(pyxel.KEY_SPACE):  # スペースキーでゲーム開始
                self.state = self.MAIN
            return

        # リトライ判定
        if pyxel.btnp(pyxel.KEY_R):
            self.init()  # OPに戻る

        # キー入力による移動
        previous_x = self.x
        previous_y = self.y
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.x -= 1
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.x += 1
        if pyxel.btnp(pyxel.KEY_UP):
            self.y -= 1
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.y += 1

        # はみ出し判定
        if self.x < 0:
            self.x = 0
        if self.x >= self.map_width:
            self.x = self.map_width - 1
        if self.y < 0:
            self.y = 0
        if self.y >= self.map_height:
            self.y = self.map_height - 1

        # 障害物への移動判定
        if self.get_map(self.x, self.y) == 1:
            self.x = previous_x
            self.y = previous_y

        # 制限時間のチェック
        elapsed_time = (pyxel.frame_count - self.start_time) / 30  # 経過時間を秒に変換
        if elapsed_time > self.time_limit:
            self.state = self.GAMEOVER  # 制限時間を超えたらゲームオーバー

        # 入力なし
        if previous_x == self.x and previous_y == self.y:
            return

        # ゲームオーバー判定
        if self.get_map(self.x, self.y) != 0:
            self.state = self.GAMEOVER

            # スコアに応じてゲームオーバー画面に登場させる猫を生成
            self.cat_num = int(self.score / 500)

            # 各猫の位置をランダムに設定
            # self.cats = []
            for _ in range(self.cat_num):
                cat_x = random.randint(0, 128 - 16)
                cat_y = random.randint(0, 128 - 16)
                cat_state = random.randint(0, 1)
                self.cats.append((cat_x, cat_y, cat_state))

        self.map[self.y][self.x] = 2  # 通過済みに設定

        # クリア判定
        if self.check_gameclear():
            # 　スコアの加算
            remaining_time = (
                self.time_limit - (pyxel.frame_count - self.start_time) / 30
            )
            num_obstacles = sum(row.count(1) for row in self.map)
            self.score += (
                self.map_width * self.map_height * (remaining_time + 5) * num_obstacles
            )

            self.current_stage += 1
            self.stage_init()  # 次のステージを初期化

    def draw(self):
        # pyxel.cls(6) #背景色

        # オープニング画面表示
        if self.state == self.OPENING:

            # 10frameに一回ランダムで動かす
            if pyxel.frame_count >= 60 and pyxel.frame_count % 30 == 0:
                self.title_positions = [
                    (x + random.randint(-1, 1), y + random.randint(-1, 1))
                    for x, y in self.title_positions
                ]

            pyxel.cls(0)  # 黒背景
            # tilemapを描画
            # 0ページ目の(0, 0)の位置から16x16のサイズ
            pyxel.bltm(0, 0, 0, 0, 0, 256, 256)

            # 各文字を個別に描画
            for i, (x, y) in enumerate(self.title_positions):
                pyxel.text(x, y, "STRAY STEPS"[i], 9, self.umplus10)

            pyxel.text(24, 80, "PRESS SPACE TO START", 7)
            return

        # スコアリザルト表示
        if self.state in [self.GAMECLEAR, self.GAMEOVER]:
            # pyxel.cls(0) #黒背景
            pyxel.bltm(0, 0, 0, 0, 0, 256, 256)  # 草原

            # 各猫の位置をランダムに移動
            for i, (cat_x, cat_y, state) in enumerate(self.cats):
                # stateは1/30の確率で変化
                if random.randint(0, 30) == 0:
                    state = state ^ 1
                    # 状態更新
                    self.cats[i] = (cat_x, cat_y, state)
                # animation
                if state == 0:
                    pyxel.blt(cat_x, cat_y, 0, 0, 0, 16, 16, 13)
                else:
                    pyxel.blt(cat_x, cat_y, 0, 16, 0, 16, 16, 13)

            pyxel.text(24, 60, f"SCORE: {int(self.score)}", 7)
            pyxel.text(24, 80, "PRESS R TO RETRY", 7)
            return

        pyxel.cls(6)  # 黒背景
        self.draw_back()
        self.draw_player()

        # 残り時間とスコア表示
        if self.state == self.MAIN:
            remaining_time = (
                self.time_limit - (pyxel.frame_count - self.start_time) / 30
            )
            pyxel.text(2, 2, f"Time: {remaining_time:.2f}", 9)
            pyxel.text(60, 2, f"Score: {int(self.score)}", 9)

    def draw_back(self):
        # 通過マスの塗りつぶし
        for x in range(self.map_width):
            for y in range(self.map_height):
                px, py = Map.to_screen(x, y)
                if self.map[y][x] == 0:
                    # 通行前は白
                    pyxel.rect(px, py, Map.SIZE, Map.SIZE, 7)
                    continue  # 塗りつぶしていない
                # print(px, py, px + Map.SIZE, py + Map.SIZE)
                if self.map[y][x] == 1:  # 障害物
                    # pyxel.rect(px, py, Map.SIZE, Map.SIZE, 8)  # 8:gray
                    # タイルマップを描画
                    # 0ページ目の(32, 0)の位置から16x16のサイズ
                    pyxel.blt(px, py, 0, 32, 0, 16, 16, 8)
                else:  # 通過済み
                    pyxel.rect(px, py, Map.SIZE, Map.SIZE, 15)

        # タイルの境界線を描画
        for i in range(self.map_width + 1):
            x1, y1 = Map.to_screen(i, 0)
            x2, y2 = Map.to_screen(i, self.map_height)
            pyxel.line(x1, y1, x2, y2, 0)
        for j in range(self.map_height + 1):
            x1, y1 = Map.to_screen(0, j)
            x2, y2 = Map.to_screen(self.map_width, j)
            pyxel.line(x1, y1, x2, y2, 0)

    def draw_player(self):
        px, py = Map.to_screen(self.x, self.y)
        # pyxel.blt(px, py, 0, 0, 0, 16, 16, 5)
        # アニメーションフレームに応じて画像を切り替え
        if self.animation_frame < 15:
            # 13(gray)が透過色
            pyxel.blt(px, py, 0, 0, 0, 16, 16, 13)  # 最初の画像
        else:
            pyxel.blt(px, py, 0, 16, 0, 16, 16, 13)  # 2つ目の画像

    def check_gameclear(self):
        if self.state == self.GAMEOVER:
            return False

        for x in range(self.map_width):
            for y in range(self.map_height):
                if self.map[y][x] == 0:
                    return False  # 塗りつぶしていない
        return True  # 全て塗りつぶした


APP()
