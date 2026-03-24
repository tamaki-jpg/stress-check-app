"""
stress_text.py
受検者ごとの評価点（ep）に基づいて、個別アドバイス文とセルフケアのポイントを生成する。

前提：全 ep は通常尺度・逆転尺度に関わらず
      1 = 最も悪い（高ストレス）、5 = 最も良い　に統一済み。
      ep <= 2 のものを「問題あり（ストレスのサインあり）」として判定する。

設計方針：
  ・各領域の合計点を主軸として「良好／中程度／高負荷」を判定し、
    受検者が状況を把握しやすい summary_text を必ず出力する
  ・良好の場合は「適正範囲内です」等の安心できるポジティブ表現を使用
  ・中程度以上の場合は ep<=2 の個別項目があればピンポイントで言及
  ・セルフケア該当ゼロの場合も温かいフォローメッセージを表示
"""

# ─────────────────────────────────────────────────────────────────────────────
# ヘルススコア変換（全軸で 1=最悪, 5=最良 に統一）
# ─────────────────────────────────────────────────────────────────────────────

# STAR軸（★）: 高ep=良好 → ep をそのまま健康スコアとして使う
# 非STAR軸（非★）: 高ep=悪い → 6-ep に変換して「高スコア=良好」に揃える
_STAR_KEYS = frozenset({
    'A6_control', 'A7_skill', 'A8_suitability', 'A9_reward',
    'B1_vigor',
    'C1_boss', 'C2_coworker', 'C3_family', 'D1_satisfaction',
})

def _health(key, ep_val):
    """
    全軸で 1=最悪, 5=最良 に正規化したヘルススコアを返す。
    STAR軸: ep をそのまま返す
    非STAR軸: 6 - ep を返す（A1-A5負担系, B2-B6症状系）
    health <= 2 を「問題あり（ストレスのサインあり）」として使う。
    """
    return ep_val if key in _STAR_KEYS else (6 - ep_val)


# ─────────────────────────────────────────────────────────────────────────────
# 各尺度：ラベル + ヘルススコア<=2 時の個別アドバイス文
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
            '不明点はそのままにせず早めに確認する習慣や、'
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
# 合計点 → レベル判定 + summary_text（必ず出力される本文）
# ─────────────────────────────────────────────────────────────────────────────

def _a_summary(sumA, a_problems):
    if sumA >= 35:
        return 'good', f'{sumA} 点　良好', (
            '仕事のストレス要因について、現在のところ適正な範囲内です。'
            'ご自身のペースで良好な状態が保たれていますので、今の働き方を継続してください。'
        )
    elif sumA >= 23:
        base = '仕事の負荷は中程度です。'
        if a_problems:
            labels = '・'.join(p['label'] for p in a_problems)
            base += f'ただし「{labels}」については引き続き注意が必要です。'
        return 'mid', f'{sumA} 点　中程度', base
    else:
        base = '仕事の負荷が高くなっています。無理をしすぎず、早めに対処することが大切です。'
        if a_problems:
            labels = '・'.join(p['label'] for p in a_problems)
            base += f'特に「{labels}」の点で強いストレスが見られます。'
        return 'high', f'{sumA} 点　高負荷', base


def _b_summary(sumB, b_problems, is_high_stress):
    if sumB >= 24:
        text = (
            '心身のストレス反応について、特に異常なサインは見られず、健康的な状態です。'
            '引き続きご自身のケアを大切にしてください。'
        )
        if is_high_stress:
            text += '　なお高ストレス者判定に該当しているため、産業医への面接指導もご検討ください。'
        return 'good', f'{sumB} 点　良好', text
    elif sumB >= 18:
        base = '心身のストレス反応は中程度です。'
        if b_problems:
            labels = '・'.join(p['label'] for p in b_problems)
            base += f'「{labels}」については意識的にセルフケアを行いましょう。'
        if is_high_stress:
            base += '産業医への面接指導もあわせてご検討ください。'
        return 'mid', f'{sumB} 点　中程度', base
    elif sumB >= 13:
        base = '心身のストレス反応が高めの状態です。十分な休息と気分転換を心がけてください。'
        if b_problems:
            labels = '・'.join(p['label'] for p in b_problems)
            base += f'「{labels}」の傾向がみられます。'
        if is_high_stress:
            base += '産業医への面接指導を積極的にご検討ください。'
        return 'high', f'{sumB} 点　高い', base
    else:
        base = '心身のストレス反応が著しく高い状態です。早急に休息を確保し、産業医への相談を強くお勧めします。'
        if b_problems:
            labels = '・'.join(p['label'] for p in b_problems)
            base += f'特に「{labels}」が顕著にみられます。'
        return 'very_high', f'{sumB} 点　著しく高い', base


def _c_summary(sumC, c_problems):
    if sumC >= 12:
        return 'good', f'{sumC} 点　充実', (
            '周囲からのサポート体制は十分に充実しています。'
            '今後も職場やご家族との良好なコミュニケーションを大切にしてください。'
        )
    elif sumC >= 7:
        base = '周囲からのサポートは中程度です。'
        if c_problems:
            parts = '・'.join(p['label'] for p in c_problems)
            base += f'「{parts}」については、困ったときに遠慮なく相談してみましょう。'
        else:
            base += '困ったことがあれば、遠慮なく周囲に声をかけてみましょう。'
        return 'mid', f'{sumC} 点　中程度', base
    else:
        base = '周囲からのサポートが不足している状態です。社内外の相談窓口の積極的な活用をご検討ください。'
        if c_problems:
            parts = '・'.join(p['label'] for p in c_problems)
            base += f'特に「{parts}」でサポートが低い傾向にあります。'
        return 'low', f'{sumC} 点　サポート不足', base


# ─────────────────────────────────────────────────────────────────────────────
# セルフケアカタログ
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
    # ヘルススコア（1=最悪, 5=最良）で統一して評価
    def h(k): return _health(k, ep.get(k, 3))

    vigor      = h('B1_vigor')       # STAR: ep直接
    fatigue    = h('B3_fatigue')     # 非STAR: 6-ep
    depression = h('B5_depression')  # 非STAR: 6-ep
    irritation = h('B2_irritation')  # 非STAR: 6-ep
    anxiety    = h('B4_anxiety')     # 非STAR: 6-ep
    physical   = h('B6_physical')    # 非STAR: 6-ep
    control    = h('A6_control')     # STAR: ep直接
    a1_qty     = h('A1_quantity')    # 非STAR: 6-ep
    c_boss     = h('C1_boss')        # STAR: ep直接
    c_coworker = h('C2_coworker')    # STAR: ep直接
    c_family   = h('C3_family')      # STAR: ep直接

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

    seen, result = set(), []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append({'key': k, **_SELFCARE_CATALOG[k]})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# メイン関数
# ─────────────────────────────────────────────────────────────────────────────

def generate_advice(ep, sumA, sumB, sumC, is_high_stress, name=''):
    """
    Parameters
    ----------
    ep            : dict  全尺度の評価点 {key: int(1-5)}
    sumA          : int   A領域ep合計 (9-45)
    sumB          : int   B領域ep合計 (6-30)
    sumC          : int   C領域ep合計 (3-15, D1除外)
    is_high_stress: bool  高ストレス判定
    name          : str   受検者の氏名（セルフケア導入文に挿入）

    Returns
    -------
    dict
      any_problems  : bool
      all_ok_message: str
      area_a        : {level, level_text, summary_text, problems:[{label,detail}]}
      area_b        : {level, level_text, summary_text, problems:[{label,detail}]}
      area_c        : {level, level_text, summary_text, problems:[{label,detail}]}
      selfcare_intro: str
      selfcare      : [{key, icon, title, items}]
    """

    # ── 問題項目を抽出（ヘルススコア <= 2 が問題あり）──────────────────────
    # health(key, ep) = ep if STAR else (6-ep) → 1=最悪, 5=最良
    # STAR非★の方向を正しく反映: 非★は ep高=悪→health低、★は ep低=悪→health低
    a_problems = [
        {'label': v['label'], 'detail': v['detail']}
        for k, v in _A_ITEMS.items() if _health(k, ep.get(k, 3)) <= 2
    ]
    b_problems = [
        {'label': v['label'], 'detail': v['detail']}
        for k, v in _B_ITEMS.items() if _health(k, ep.get(k, 3)) <= 2
    ]
    c_problems = [
        {'label': v['label'], 'detail': v['detail']}
        for k, v in _C_ITEMS.items() if _health(k, ep.get(k, 3)) <= 2
    ]

    # ── 合計点 → レベル + summary_text ─────────────────────────────────────
    a_level, a_level_text, a_summary_text = _a_summary(sumA, a_problems)
    b_level, b_level_text, b_summary_text = _b_summary(sumB, b_problems, is_high_stress)
    c_level, c_level_text, c_summary_text = _c_summary(sumC, c_problems)

    # 高ストレス判定の場合は B 領域 problems に産業医誘導カードを先頭追加
    # （B の summary_text にも記載済みだが、問題項目として視覚的に目立たせる）
    if is_high_stress and b_level in ('very_high', 'high'):
        b_problems.insert(0, {
            'label': '【高ストレス者判定】産業医への面接指導について',
            'detail': (
                '今回の判定では高ストレス者に該当しています。'
                '産業医による面接指導は無料で受けられ、評価に影響しません。'
                '希望される場合は人事担当者または実施者にお申し出ください。'
            ),
        })

    # ── 全体の問題有無 ────────────────────────────────────────────────────
    any_problems = bool(a_problems or b_problems or c_problems)

    all_ok_message = (
        '今回のストレスチェック結果において、客観的に見て著しくケアが必要な項目は'
        '見当たりませんでした。心身ともに適正な範囲内の状態が保たれています。'
        'ご自身の良い状態を継続するために、引き続きセルフケアをお忘れなく。'
    )

    # ── セルフケア ────────────────────────────────────────────────────────
    selfcare = _build_selfcare(ep, sumA, is_high_stress)

    # 繋ぎの文（受検者の氏名を動的に挿入）
    name_part = f'{name} さん' if name else 'あなた'
    if any_problems:
        selfcare_intro = (
            f'上記で挙げた {name_part} のストレスのサインに対して、'
            '以下のセルフケアを参考にしてみてください。'
        )
    else:
        selfcare_intro = (
            f'{name_part} の現在の状態に特に問題は見当たりませんが、'
            '良好な状態を維持するために以下を継続してください。'
        )

    # セルフケアが 0 件（全良好 & 非高ストレス）の場合はメッセージカードを表示
    if not selfcare:
        selfcare = [{
            'key': 'all_good',
            'icon': '✅',
            'title': '良好な状態を継続してください',
            'items': [
                '現在、心身ともに適正な範囲内であり、特筆すべき強いストレスサインは見られません。',
                '今の良好な生活習慣や働き方を継続し、'
                '次回のストレスチェックもご自身の健康管理に役立ててください。',
            ],
        }]

    return {
        'any_problems':   any_problems,
        'all_ok_message': all_ok_message,
        'area_a': {
            'level':        a_level,
            'level_text':   a_level_text,
            'summary_text': a_summary_text,
            'problems':     a_problems,
        },
        'area_b': {
            'level':        b_level,
            'level_text':   b_level_text,
            'summary_text': b_summary_text,
            'problems':     b_problems,
        },
        'area_c': {
            'level':        c_level,
            'level_text':   c_level_text,
            'summary_text': c_summary_text,
            'problems':     c_problems,
        },
        'selfcare_intro': selfcare_intro,
        'selfcare':       selfcare,
    }
