from textwrap import dedent

from decodiff._git_diff.parse_unified_diff import parse_unified_diff


def test_parse_unified_diff_1():
    diff_text = dedent("""
        diff --git a/tests/_res/file1.md b/tests/_res/file1.md
        index 79271ac..4b916cd 100644
        --- a/tests/_res/file1.md
        +++ b/tests/_res/file1.md
        @@ -34 +33,0 @@ git status
        -git add
        @@ -35,0 +35 @@ git commit
        +git log
        @@ -42,0 +43 @@ Intented code block.
        +    git log
        @@ -53 +53,0 @@ Intented code block.
        -    * nasted item2
        @@ -69 +72 @@ Intented code block.
        -Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        +Lorem ipsum dolor sit amet, ADD WORDS consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        @@ -72,0 +76,2 @@ Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliqu
        +Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        +
        """).strip()
    changed = parse_unified_diff(diff_text)

    assert changed[0].from_file == "tests/_res/file1.md"
    assert changed[0].to_file == "tests/_res/file1.md"
    assert changed[0].changed_lines[0].anchor_no == 0
    assert changed[0].changed_lines[0].line_no == 35
    assert changed[0].changed_lines[0].col_start == 0
    assert changed[0].changed_lines[0].col_end == 7

    assert changed[0].changed_lines[1].anchor_no == 1
    assert changed[0].changed_lines[1].line_no == 43
    assert changed[0].changed_lines[1].col_start == 0
    assert changed[0].changed_lines[1].col_end == 11

    assert changed[0].changed_lines[2].anchor_no == 2
    assert changed[0].changed_lines[2].line_no == 72
    assert changed[0].changed_lines[2].col_start == 0
    assert changed[0].changed_lines[2].col_end == 133

    assert changed[0].changed_lines[3].anchor_no == 3
    assert changed[0].changed_lines[3].line_no == 76
    assert changed[0].changed_lines[3].col_start == 0
    assert changed[0].changed_lines[3].col_end == 102

    assert changed[0].changed_lines[4].anchor_no == 4
    assert changed[0].changed_lines[4].line_no == 77
    assert changed[0].changed_lines[4].col_start == 0
    assert changed[0].changed_lines[4].col_end == 0


def test_parse_unified_diff_2():
    diff_text = dedent("""
        diff --git a/tests/_res/file1.md b/tests/_res/file1.md
        index 79271ac..4b916cd 100644
        --- a/tests/_res/file1.md
        +++ b/tests/_res/file1.md
        @@ -34 +33,0 @@ git status
        -git add
        @@ -35,0 +35 @@ git commit
        +git log
        diff --git a/tests/_res/subdir/file2.md b/tests/_res/subdir/file2.md
        new file mode 100644
        index 0000000..cf6ad9e
        --- /dev/null
        +++ b/tests/_res/subdir/file2.md
        @@ -0,0 +1,11 @@
        +# file 2
        +
        +## 1
        +
        +ジョバンニはまっ赤かになってうなずきました。けれどもいつかジョバンニの眼めのなかには涙なみだがいっぱいになりました。そうだ僕ぼくは知っていたのだ、もちろんカムパネルラも知っている、それはいつかカムパネルラのお父さんの博士はかせのうちでカムパネルラといっしょに読んだ雑誌ざっしのなかにあったのだ。
        +
        +それどこでなくカムパネルラは、その雑誌ざっしを読むと、すぐお父さんの書斎しょさいから巨おおきな本をもってきて、ぎんがというところをひろげ、まっ黒な頁ページいっぱいに白に点々てんてんのある美うつくしい写真しゃしんを二人でいつまでも見たのでした。
        +
        +## 2
        +
        +ジョバンニが学校の門を出るとき、同じ組の七、八人は家へ帰らずカムパネルラをまん中にして校庭こうていの隅すみの桜さくらの木のところに集あつまっていました。それはこんやの星祭ほしまつりに青いあかりをこしらえて川へ流ながす烏瓜からすうりを取とりに行く相談そうだんらしかったのです。
        diff --git a/tests/_res/subdir/file3-rm.md b/tests/_res/subdir/file3-rm.md
        deleted file mode 100644
        index c5a319c..0000000
        --- a/tests/_res/subdir/file3-rm.md
        +++ /dev/null
        @@ -1,5 +0,0 @@
        -# file 3
        -
        -吾輩わがはいは猫である。名前はまだ無い。
        -
        -どこで生れたかとんと見当けんとうがつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。吾輩はここで始めて人間というものを見た。しかもあとで聞くとそれは書生という人間中で一番獰悪どうあくな種族であったそうだ。
        diff --git a/tests/_res/subdir/file4-mode.md b/tests/_res/subdir/file4-mode.md
        old mode 100644
        new mode 100755
        """).strip()
    changed = parse_unified_diff(diff_text)

    assert changed[0].from_file == "tests/_res/file1.md"
    assert changed[0].to_file == "tests/_res/file1.md"
    assert changed[0].changed_lines[0].anchor_no == 0
    assert changed[0].changed_lines[0].line_no == 35
    assert changed[0].changed_lines[0].col_start == 0
    assert changed[0].changed_lines[0].col_end == 7
    assert len(changed[0].changed_lines) == 1

    assert changed[1].from_file is None
    assert changed[1].to_file == "tests/_res/subdir/file2.md"
    assert len(changed[1].changed_lines) == 0

    assert changed[2].from_file == "tests/_res/subdir/file3-rm.md"
    assert changed[2].to_file is None
    assert len(changed[2].changed_lines) == 0

    assert len(changed) == 3
