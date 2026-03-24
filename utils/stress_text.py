"""
stress_text.py
受検者ごとの評価点（ep）に基づいて、個別アドバイス文とセルフケアのポイントを生成する。

前提：全 ep は通常尺度・逆転尺度に関わらず
      1 = 最も悪い（高ストレス）、5 = 最も良い　に統一済み。
      ep <= 2 のものを「問題あり（ストレスのサインあり）」として判定する。

改訂方針：
  ・合計点によるざっくり評価は冒頭の一言にとどめる
  ・ep<=2 の個別項目を最優先でピックアップし、項目ごとのピンポイントアドバイスを出力
  ・セルフケア欄は「上記で挙げたサインに対して」という文脈で繋ぐ
  ・ep<=2 が1つもない場合は肯定的フォローを出力
"""

# ─────────────────────────────────────────────────────────────────────────────
# 各尺度：ラベル + 個別アドバイス文
# ─────────────────────────────────────────────────────────────────────────────

_A_ITEMS = {
    'A1_quantity': {
        'label':  '仕事の量的負担（量的過負荷）',
        'detail': (
            '仕事の量が現在のキャパシティを超えている可能性があります。'
            '業務の優先順位づけを行い、こなしきれない仕事については'
            '上司や同僚に状況を共有・相談することを検討してください。'
        ),
    },
    'A2_quality': {
        'label':  '仕事の質的負担（質的過負荷）',
        'detail': (
            '仕事の難易度・複雑さが精神的な負荷となっています。'
            '不明点をそのままにせず早めに確認する習慣や、'
            '必要であればサポートを求めることが重要です。'
        ),
    },
    'A3_physical': {
        'label':  '身体的な作業負担',
        'detail': (
            '身体的な作業負荷が大きい状態です。'
            '姿勢・作業環境（照明・温度・騒音）の改善や、'
            '定期的なストレッチ・適切な休憩を取ることを意識してください。'
        ),
    },
    'A4_interpersonal': {
        'label':  '職場の対人関係ストレス',
        'detail': (
            '職場の人間関係で強いストレスを感じています。'
            '当事者同士での解決が難しい場合は、早めに第三者（人事担当者や別の管理職）へ'
            '客観的な状況を共有することを検討してください。'
        ),
    },
    'A5_environment': {
        'label':  '職場の物理的な環境',
        'detail': (
            '職場の物理的な環境（騒音・温度・レイアウト等）がストレスの原因になっています。'
            '改善できる点があれば具体的に担当者や上司に伝えてみましょう。'
        ),
    },
    'A6_control': {
        'label':  '仕事のコントロール度（裁量権の低さ）',
        'detail': (
            '自分のペースや方法で仕事を進めにくく、窮屈さを感じているようです。'
            '小さなことでも自分で決定できる範囲を増やす工夫や、'
            '仕事の進め方についての裁量を上司に相談してみましょう。'
        ),
    },
    'A7_skill': {
        'label':  '技能・スキルの活用度',
        'detail': (
            '自分のスキルや経験が十分に活かせていないと感じています。'
            '得意なことを活かせる業務への関与を求めたり、'
            '自分の意向を上司に共有することを検討してみましょう。'
        ),
    },
    'A8_suitability': {
        'label':  '仕事の適性度',
        'detail': (
            '現在の仕事と自分の適性・志向のギャップを感じているようです。'
            '長期的には業務内容の見直しや異動相談も選択肢の一つです。'
            'まずは信頼できる上司や人事に気持ちを話してみましょう。'
        ),
    },
    'A9_reward': {
        'label':  '働きがい・達成感',
        'detail': (
            '働きがいや達成感が感じられにくい状態です。'
            '小さな成果でも意識的に確認する習慣や、'
            '自分なりの「やりがい」を見つける目標設定をしてみましょう。'
        ),
    },
}

_B_ITEMS = {
    'B1_vigor': {
        'label':  '活気の低下',
        'detail': (
            '気力や意欲が低下している状態が続いており心配です。'
            '無理に頑張ろうとせず、まず十分な休息を確保することが先決です。'
            '改善が見られない場合は、産業医や専門の相談窓口を頼ってください。'
        ),
    },
    'B2_irritation': {
        'label':  'イライラ感の高まり',
        'detail': (
            '感情面での張り詰めた状態が続いています。'
            '腹式呼吸・入浴・音楽鑑賞など自分に合ったリラクセーション法を取り入れ、'
            '意識的に「仕事から完全に離れる時間」を作ることが大切です。'
        ),
    },
    'B3_fatigue': {
        'label':  '強い疲労感',
        'detail': (
            '強い疲労感が出ています。'
            '心身のエネルギーが枯渇しつつあるサインであるため、'
            'まずは十分な睡眠と休息をとることを【最優先】にしてください。'
            '疲れを「気力でカバー」しようとすることは禁物です。'
        ),
    },
    'B4_anxiety': {
        'label':  '不安感の高まり',
        'detail': (
            '漠然とした不安感や緊張感が高まっています。'
            '「現状を書き出す」「誰かに話す」ことで状況を俯瞰し、'
            'リラクセーションで心身を意図的にほぐす時間を設けてください。'
        ),
    },
    'B5_depression': {
        'label':  '抑うつ感・気分の落ち込み',
        'detail': (
            '気分の落ち込みや、やる気が起きない状態が続いており心配です。'
            '無理に頑張ろうとせず、必要に応じて産業医や専門の相談窓口を頼ってください。'
            '早めのサポートが回復を早めます。'
        ),
    },
    'B6_physical': {
        'label':  '身体愁訴（頭痛・肩こり・胃腸不調等）',
        'detail': (
            '頭痛・肩こり・胃腸不調など、身体的なサインが出ています。'
            'これらは心身の疲弊を示すシグナルであることが多いです。'
            'まずは十分な睡眠と休息を【最優先】にし、'
            '症状が続く場合は医療機関への受診も検討してください。'
        ),
    },
}

_C_ITEMS = {
    'C1_boss': {
        'label':  '上司からのサポート不足',
        'detail': (
            '上司との関係で困ったときに助けを求めにくい状況のようです。'
            '職場内での解決が難しい場合は、社外の相談窓口（こころの耳など）を'
            '積極的に活用し、一人で抱え込まない仕組みを作ってください。'
        ),
    },
    'C2_coworker': {
        'label':  '同僚からのサポート不足',
        'detail': (
            '同僚との連携やサポートが感じにくい状況のようです。'
            '小さなことから声をかけ合う習慣や、ランチ等の雑談でつながりを作ることも助けになります。'
            '職場内の改善が難しければ、社外の相談窓口も活用してください。'
        ),
    },
    'C3_family': {
        'label':  '家族・友人からのサポート不足',
        'detail': (
            '職場外（家族・友人）のサポートが得にくい状況のようです。'
            '信頼できる人に話を聞いてもらうことは心理的な負荷を大きく減らします。'
            '外部の相談窓口（こころの耳メール・電話相談）の活用も検討してみましょう。'
        ),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 合計点 → 一言評価文
# ─────────────────────────────────────────────────────────────────────────────

def _a_level_info(sumA):
    if sumA <= 22:
        return 'high',     f'合計 {sumA} 点 ─ 全体的に負荷が高い状態（要注意）'
    elif sumA <= 34:
        return 'mid',      f'合計 {sumA} 点 ─ 一部負荷あり、概ね普通の範囲'
    else:
        return 'good',     f'合計 {sumA} 点 ─ 全体的に良好な状態'


def _b_level_info(sumB):
    if sumB <= 12:
        return 'very_high', f'合計 {sumB} 点 ─ 心身の反応が著しく高い（高ストレス判定条件に相当）'
    elif sumB <= 17:
        return 'high',      f'合計 {sumB} 点 ─ 心身の反応が高め（要注意）'
    elif sumB <= 23:
        return 'mid',       f'合計 {sumB} 点 ─ 中程度、一部注意が必要'
    else:
        return 'good',      f'合計 {sumB} 点 ─ 良好な状態'


def _c_level_info(sumC):
    if sumC <= 6:
        return 'low',  f'合計 {sumC} 点 ─ サポートが不足している状態'
    elif sumC <= 11:
        return 'mid',  f'合計 {sumC} 点 ─ 概ね普通、一部注意'
    else:
        return 'good', f'合計 {sumC} 点 ─ サポートが充実している状態'


# ─────────────────────────────────────────────────────────────────────────────
# セルフケアカタログ（キーと条件の対応）
# ─────────────────────────────────────────────────────────────────────────────

_SELFCARE_CATALOG = {
    'sleep': {
        'icon': '🌙', 'title': '睡眠の改善',
        'items': [
            '疲労回復のために毎日十分な睡眠を確保する',
            '眠くなってから就床し、起床時間を一定に保つ',
            '午後の短い昼寝（15〜30分）を活用する',
            '就寝前3〜4時間はカフェイン摂取を避ける',
            '寝酒は睡眠の質を下げるため控える',
        ],
    },
    'food': {
        'icon': '🍱', 'title': '食事の見直し',
        'items': [
            '青魚（DHA・EPA）に含まれる脂肪酸は抗うつ効果が期待できる',
            '緑黄色野菜の葉酸はメンタルヘルスに重要な栄養素',
            '良質なたんぱく質（肉・魚・大豆）を毎食摂取する',
            '朝食を摂ることで体内リズムを整える',
            '夕食は就寝2時間前までに済ませる',
        ],
    },
    'exercise': {
        'icon': '🚶', 'title': '適度な運動',
        'items': [
            '息が上がらない程度の有酸素運動（ウォーキング等）が効果的',
            '1日60分・約8,000歩を目安にする',
            '「今より10分多く歩く」ことから無理なく始める',
            '運動はストレスホルモンの低減と睡眠改善にも効果的',
        ],
    },
    'relaxation': {
        'icon': '🧘', 'title': 'リラクセーション',
        'items': [
            '腹式呼吸・アロマ・入浴・音楽など自分に合った方法を見つける',
            '考え方のクセ（自分を責めすぎる等）に気づくことも有効',
            '「現状を書き出す」「誰かに話す」で状況を俯瞰する',
            'ストレッサーと距離を置く時間（趣味・散歩）を意識的に確保する',
        ],
    },
    'action': {
        'icon': '📋', 'title': '行動の工夫',
        'items': [
            'ストレスの原因を書き出して分解・整理する',
            '影響の大きいものから解決策をリストアップする',
            '実行しやすい方法から試してみる',
            '上司・同僚への相談や業務分担の見直しも有効',
        ],
    },
    'consultation': {
        'icon': '📞', 'title': '相談窓口の活用',
        'items': [
            '一人で抱え込まず、早めに相談することが大切',
            'こころの耳 電話相談：0120-565-455（平日17〜22時・土日10〜16時）',
            'SNS相談・メール相談（24時間受付・1週間以内返信）も利用可',
            '産業医による面接指導は無料・評価に影響なし',
        ],
    },
}


def _build_selfcare(ep, sumA, is_high_stress):
    """ep<=2 の項目に基づいてセルフケアキーを選択し返す"""
    vigor      = ep.get('B1_vigor', 3)
    fatigue    = ep.get('B3_fatigue', 3)
    depression = ep.get('B5_depression', 3)
    irritation = ep.get('B2_irritation', 3)
    anxiety    = ep.get('B4_anxiety', 3)
    physical   = ep.get('B6_physical', 3)
    control    = ep.get('A6_control', 3)
    a1_qty     = ep.get('A1_quantity', 3)
    c_boss     = ep.get('C1_boss', 3)
    c_coworker = ep.get('C2_coworker', 3)
    c_family   = ep.get('C3_family', 3)

    keys = []

    if fatigue <= 2 or vigor <= 2 or physical <= 2:
        keys.append('sleep')
    if depression <= 2 or vigor <= 2:
        keys.append('food')
    if fatigue <= 2 or vigor <= 2 or depression <= 2:
        keys.append('exercise')
    if irritation <= 2 or anxiety <= 2:
        keys.append('relaxation')
    if a1_qty <= 2 or control <= 2 or sumA <= 22:
        keys.append('action')
    if c_boss <= 2 or c_coworker <= 2 or c_family <= 2 or is_high_stress:
        keys.append('consultation')

    # 重複除去（順序維持）
    seen = set()
    result = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append({'key': k, **_SELFCARE_CATALOG[k]})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# メイン関数
# ─────────────────────────────────────────────────────────────────────────────

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
    dict
      any_problems  : bool
      all_ok_message: str   (any_problems=False の場合に表示)
      area_a        : {level, level_text, problems:[{label,detail}]}
      area_b        : {level, level_text, problems:[{label,detail}]}
      area_c        : {level, level_text, problems:[{label,detail}]}
      selfcare_intro: str
      selfcare      : [{key, icon, title, items}]
    """

    # ── A領域 ────────────────────────────────────────────────────────────────
    a_level, a_level_text = _a_level_info(sumA)
    a_problems = [
        {'label': info['label'], 'detail': info['detail']}
        for key, info in _A_ITEMS.items()
        if ep.get(key, 3) <= 2
    ]

    # ── B領域 ────────────────────────────────────────────────────────────────
    b_level, b_level_text = _b_level_info(sumB)
    b_problems = [
        {'label': info['label'], 'detail': info['detail']}
        for key, info in _B_ITEMS.items()
        if ep.get(key, 3) <= 2
    ]
    # 高ストレス判定の場合は産業医誘導を B の先頭に追加
    if is_high_stress and not any(
        ep.get(k, 3) <= 2 for k in ('B1_vigor', 'B5_depression')
    ):
        b_problems.insert(0, {
            'label': '【高ストレス者判定】産業医への面接指導について',
            'detail': (
                '今回の判定では高ストレス者に該当しています。'
                '産業医による面接指導は無料で受けられ、評価に影響しません。'
                '希望される場合は人事担当者または実施者にお申し出ください。'
            ),
        })

    # ── C領域 ────────────────────────────────────────────────────────────────
    c_level, c_level_text = _c_level_info(sumC)
    c_problems = [
        {'label': info['label'], 'detail': info['detail']}
        for key, info in _C_ITEMS.items()
        if ep.get(key, 3) <= 2
    ]

    # ── 全体の問題有無 ────────────────────────────────────────────────────────
    all_problems = a_problems + b_problems + c_problems
    any_problems = len(all_problems) > 0

    all_ok_message = (
        '現在、客観的に見て著しくケアが必要な項目は見当たりません。'
        'ご自身の良い状態を保つために、今後もセルフケアを継続してください。'
    )

    # ── セルフケア ────────────────────────────────────────────────────────────
    selfcare = _build_selfcare(ep, sumA, is_high_stress)

    # 繋ぎの文（問題あり/なしで分岐）
    if any_problems:
        problem_labels = [p['label'] for p in all_problems[:3]]
        label_str = '・'.join(problem_labels)
        suffix = '等' if len(all_problems) > 3 else ''
        selfcare_intro = (
            f'上記で挙げた「{label_str}{suffix}」のサインに対して、'
            '以下のセルフケアを参考にしてみてください。'
        )
    else:
        selfcare_intro = (
            '現在特に問題は見当たりませんが、'
            '良好な状態を維持するために以下のセルフケアを継続してください。'
        )

    # セルフケアが0件の場合（全良好 & 高ストレスでもない）
    if not selfcare:
        selfcare = [{
            'key': 'default', 'icon': '✅', 'title': '現状維持',
            'items': ['現在の生活習慣を継続し、定期的にストレスチェックを活用してください。'],
        }]

    return {
        'any_problems':   any_problems,
        'all_ok_message': all_ok_message,
        'area_a': {
            'level':      a_level,
            'level_text': a_level_text,
            'problems':   a_problems,
        },
        'area_b': {
            'level':      b_level,
            'level_text': b_level_text,
            'problems':   b_problems,
        },
        'area_c': {
            'level':      c_level,
            'level_text': c_level_text,
            'problems':   c_problems,
        },
        'selfcare_intro': selfcare_intro,
        'selfcare':       selfcare,
    }
