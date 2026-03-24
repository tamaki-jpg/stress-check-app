"""
stress_text.py
受検者ごとの評価点（ep）に基づいて、個別アドバイス文とセルフケアのポイントを生成する。

前提：全 ep は通常尺度・逆転尺度に関わらず
      1 = 最も悪い（高ストレス）、5 = 最も良い　に統一済み。
      ep <= 2 のものを「問題あり」として判定する。
"""


# ── 各尺度の日本語ラベル ─────────────────────────────────────────────────────
_A_LABELS = {
    'A1_quantity':      '仕事の量的負担が多い',
    'A2_quality':       '仕事の質的負担が高い',
    'A3_physical':      '身体的な負担が大きい',
    'A4_interpersonal': '職場の対人関係でのストレスがある',
    'A5_environment':   '職場の物理的な環境に問題がある',
    'A6_control':       'コントロール度（裁量）が低い',
    'A7_skill':         '技能が十分に活用されていない',
    'A8_suitability':   '仕事の適性が感じられにくい',
    'A9_reward':        '働きがいが感じられにくい',
}
_B_LABELS = {
    'B1_vigor':      '活気の低下がみられる',
    'B2_irritation': 'イライラ感が高まっている',
    'B3_fatigue':    '強い疲労感がある',
    'B4_anxiety':    '不安感が強い',
    'B5_depression': '抑うつ感がある',
    'B6_physical':   '身体愁訴（身体の不調）がある',
}


def _problems(ep, label_dict):
    """ep <= 2 の項目ラベルリストを返す"""
    return [label for key, label in label_dict.items() if ep.get(key, 3) <= 2]


def _join(items):
    return '「' + '」「'.join(items) + '」'


def generate_advice(ep, sumA, sumB, sumC, is_high_stress):
    """
    Parameters
    ----------
    ep            : dict  全尺度の評価点 {key: int(1-5)}
    sumA          : int   A領域ep合計 (9-45)
    sumB          : int   B領域ep合計 (6-30)
    sumC          : int   C領域ep合計 (3-15, D1除外)
    is_high_stress: bool  高ストレス判定

    Returns
    -------
    dict:
      area_a  : {level, text}
      area_b  : {level, text}
      area_c  : {level, text}
      selfcare: [{key, icon, title, items:[str]}]
    """

    # ── A領域 ────────────────────────────────────────────────────────────────
    a_probs = _problems(ep, _A_LABELS)
    if sumA <= 22:
        a_level = 'high'
        a_text = 'ストレスの原因となる仕事上の負担が全体的に大きい状態です（要注意）。'
        if a_probs:
            a_text += ('特に' + _join(a_probs) + 'といった点が懸念されます。'
                       '業務量の調整や上司・同僚への相談を検討してください。')
        else:
            a_text += '業務の見直しや十分な休息の確保を意識してみましょう。'
    elif sumA <= 34:
        a_level = 'mid'
        a_text = 'ストレスの原因はやや見られますが、全体的には概ね普通の範囲内です。'
        if a_probs:
            a_text += (_join(a_probs) + 'については引き続き注意が必要です。')
    else:
        a_level = 'good'
        a_text = ('ストレスの原因となる仕事上の負担は全体的に良好な状態です。'
                  '現状を維持しながら、変化があれば早めに対処しましょう。')

    # ── B領域 ────────────────────────────────────────────────────────────────
    b_probs = _problems(ep, _B_LABELS)
    if sumB <= 12:
        b_level = 'very_high'
        b_text = '心身のストレス反応が著しく高い状態です（高ストレス判定の条件に相当）。'
        if b_probs:
            b_text += (_join(b_probs) + 'が顕著にみられます。')
        b_text += '早急に休息を確保し、産業医への相談を強くお勧めします。'
    elif sumB <= 17:
        b_level = 'high'
        b_text = '心身のストレス反応が高めの状態です（要注意）。'
        if b_probs:
            b_text += (_join(b_probs) + 'の傾向がみられます。')
        b_text += '十分な休息と気分転換を心がけてください。'
        if is_high_stress:
            b_text += '産業医への面接指導もご検討ください。'
    elif sumB <= 23:
        b_level = 'mid'
        b_text = '心身のストレス反応は中程度の状態です。'
        if b_probs:
            b_text += (_join(b_probs) + 'について意識的にセルフケアを行いましょう。')
        else:
            b_text += '引き続きセルフケアを継続してください。'
    else:
        b_level = 'good'
        b_text = '心身のストレス反応は良好な状態です。現状の生活習慣を維持しましょう。'

    # 高ストレス判定の場合は産業医誘導を付加（b_level が very_high 以外）
    if is_high_stress and b_level not in ('very_high', 'high'):
        b_text += '　なお、高ストレス者判定に該当しているため、産業医への面接指導をお勧めします。'

    # ── C領域 ────────────────────────────────────────────────────────────────
    c_boss     = ep.get('C1_boss', 3) <= 2
    c_coworker = ep.get('C2_coworker', 3) <= 2
    c_family   = ep.get('C3_family', 3) <= 2
    c_low_parts = ((['上司'] if c_boss else []) +
                   (['同僚'] if c_coworker else []) +
                   (['家族・友人'] if c_family else []))
    if sumC <= 6:
        c_level = 'low'
        c_text = '周囲からのサポートが不足している状態です。'
        if c_low_parts:
            c_text += '特に「' + '・'.join(c_low_parts) + '」からのサポートが低い傾向にあります。'
        c_text += '社内外の相談窓口の積極的な活用をご検討ください。'
    elif sumC <= 11:
        c_level = 'mid'
        c_text = '周囲からのサポートは概ね普通の状態です。'
        if c_low_parts:
            c_text += '「' + '・'.join(c_low_parts) + '」との関係で困ったときは、遠慮なく相談してみましょう。'
        else:
            c_text += '困ったことがあれば、遠慮なく周囲に相談しましょう。'
    else:
        c_level = 'good'
        c_text = ('周囲からのサポートが充実しています。'
                  '良好な人間関係を大切にし、引き続き周囲との関係を維持しましょう。')

    # ── セルフケアのポイント ──────────────────────────────────────────────────
    vigor      = ep.get('B1_vigor', 3)
    fatigue    = ep.get('B3_fatigue', 3)
    depression = ep.get('B5_depression', 3)
    irritation = ep.get('B2_irritation', 3)
    anxiety    = ep.get('B4_anxiety', 3)
    physical   = ep.get('B6_physical', 3)
    control    = ep.get('A6_control', 3)
    a1_qty     = ep.get('A1_quantity', 3)

    selfcare = []

    # 睡眠
    if fatigue <= 2 or vigor <= 2 or physical <= 2:
        selfcare.append({
            'key': 'sleep', 'icon': '🌙', 'title': '睡眠の改善',
            'items': [
                '疲労回復のために毎日十分な睡眠を確保する',
                '眠くなってから就床し、起床時間を一定に保つ',
                '午後の短い昼寝（15〜30分）を活用する',
                '就寝前3〜4時間はカフェイン摂取を避ける',
                '寝酒は睡眠の質を下げるため控える',
            ]
        })

    # 食事
    if depression <= 2 or vigor <= 2:
        selfcare.append({
            'key': 'food', 'icon': '🍱', 'title': '食事の見直し',
            'items': [
                '青魚（DHA・EPA）に含まれる脂肪酸は抗うつ効果が期待できる',
                '緑黄色野菜の葉酸はメンタルヘルスに重要な栄養素',
                '良質なたんぱく質（肉・魚・大豆）を毎食摂取する',
                '朝食を摂ることで体内リズムを整える',
                '夕食は就寝2時間前までに済ませる',
            ]
        })

    # 運動
    if fatigue <= 2 or vigor <= 2 or depression <= 2:
        selfcare.append({
            'key': 'exercise', 'icon': '🚶', 'title': '適度な運動',
            'items': [
                '息が上がらない程度の有酸素運動（ウォーキング等）が効果的',
                '1日60分・約8,000歩を目安にする',
                '「今より10分多く歩く」ことから無理なく始める',
                '運動はストレスホルモンの低減と睡眠改善にも効果的',
            ]
        })

    # リラクセーション
    if irritation <= 2 or anxiety <= 2:
        selfcare.append({
            'key': 'relaxation', 'icon': '🧘', 'title': 'リラクセーション',
            'items': [
                '腹式呼吸・アロマ・入浴・音楽など自分に合った方法を見つける',
                '考え方のクセ（自分を責めすぎる等）に気づくことも有効',
                '「現状を書き出す」「誰かに話す」で状況を俯瞰する',
                'ストレッサーと距離を置く時間（趣味・散歩）を意識的に確保する',
            ]
        })

    # 行動の工夫
    if a1_qty <= 2 or control <= 2 or sumA <= 22:
        selfcare.append({
            'key': 'action', 'icon': '📋', 'title': '行動の工夫',
            'items': [
                'ストレスの原因を書き出して分解・整理する',
                '影響の大きいものから解決策をリストアップする',
                '実行しやすい方法から試してみる',
                '上司・同僚への相談や業務分担の見直しも有効',
            ]
        })

    # 相談窓口
    any_c_low = c_boss or c_coworker or c_family
    if any_c_low or is_high_stress or sumC <= 11:
        selfcare.append({
            'key': 'consultation', 'icon': '📞', 'title': '相談窓口の活用',
            'items': [
                '一人で抱え込まず、早めに相談することが大切',
                'こころの耳 電話相談：0120-565-455（平日17〜22時・土日10〜16時）',
                'SNS相談・メール相談（24時間受付・1週間以内返信）も利用可',
                '産業医による面接指導は無料・評価に影響なし',
            ]
        })

    # 該当なし → デフォルト
    if not selfcare:
        selfcare = [{
            'key': 'default', 'icon': '✅', 'title': '現状維持',
            'items': ['現在の生活習慣を継続し、定期的にストレスチェックを活用してください。']
        }]

    return {
        'area_a':  {'level': a_level,  'text': a_text},
        'area_b':  {'level': b_level,  'text': b_text},
        'area_c':  {'level': c_level,  'text': c_text},
        'selfcare': selfcare,
    }
