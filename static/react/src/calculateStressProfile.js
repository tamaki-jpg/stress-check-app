import conversionTable from './conversionTable.json';

/**
 * ストレスチェック（57項目）の回答から評価点と高ストレス判定を算出する
 *
 * @param {Object} answers  { q1: 1, q2: 4, ..., q57: 2 }  全質問の回答値（1〜4）
 * @param {string} gender   'male' | 'female'
 * @returns {{ isHighStress, summaryScores, radarChartData }}
 */
export function calculateStressProfile(answers, gender) {
  // ─────────────────────────────────────────────────────
  // 1. 素点の計算
  //    ・高い素点＝「その特性が強い」方向
  //    ・A/C 領域の逆転項目は (5 - 回答) or (15 - 合計) で処理
  // ─────────────────────────────────────────────────────
  const q = answers; // 短縮エイリアス

  const rawScores = {
    // ── 領域A：仕事のストレス要因 (q1〜q17) ──────────────
    A1_quantity:      15 - (q.q1  + q.q2  + q.q3),   // 量的負担
    A2_quality:       15 - (q.q4  + q.q5  + q.q6),   // 質的負担
    A3_physical:       5 -  q.q7,                      // 身体的負担
    A6_control:       15 - (q.q8  + q.q9  + q.q10),  // コントロール
    A7_skill:               q.q11,                     // 技術の活用
    A4_interpersonal: 10 - (q.q12 + q.q13) + q.q14,  // 対人関係
    A5_environment:    5 -  q.q15,                     // 職場環境
    A8_suitability:    5 -  q.q16,                     // 適合性
    A9_reward:         5 -  q.q17,                     // 働きがい

    // ── 領域B：心身のストレス反応 (q18〜q46) ─────────────
    // q18〜q20: 活気（高値＝活気あり）
    B1_vigor:          q.q18 + q.q19 + q.q20,
    // q21〜q23: イライラ感（高値＝ストレス高）
    B2_irritation:     q.q21 + q.q22 + q.q23,
    // q24〜q26: 疲労感
    B3_fatigue:        q.q24 + q.q25 + q.q26,
    // q27〜q29: 不安感
    B4_anxiety:        q.q27 + q.q28 + q.q29,
    // q30〜q35: 抑うつ感（6項目）
    B5_depression:     q.q30 + q.q31 + q.q32 + q.q33 + q.q34 + q.q35,
    // q36〜q46: 身体愁訴（11項目）
    B6_physical:       q.q36 + q.q37 + q.q38 + q.q39 + q.q40 +
                       q.q41 + q.q42 + q.q43 + q.q44 + q.q45 + q.q46,

    // ── 領域C：周囲のサポート (q47〜q55) ─────────────────
    // 各 3 問の合計を 15 から引く（低回答＝サポートあり → 高素点）
    C1_boss:     15 - (q.q47 + q.q50 + q.q53), // 上司サポート
    C2_coworker: 15 - (q.q48 + q.q51 + q.q54), // 同僚サポート
    C3_family:   15 - (q.q49 + q.q52 + q.q55), // 家族・友人サポート
  };

  // ─────────────────────────────────────────────────────
  // 2. 素点 → 評価点（1〜5）変換
  // ─────────────────────────────────────────────────────
  const getEvalPoint = (key, raw) => {
    const table = conversionTable[gender]?.[key];
    if (!table) return 3; // フォールバック
    const match = table.find(t => raw >= t.min && raw <= t.max);
    return match ? match.point : 3;
  };

  const evalScores = {};
  let sumA = 0, sumB = 0, sumC = 0;

  for (const [key, raw] of Object.entries(rawScores)) {
    const pt = getEvalPoint(key, raw);
    evalScores[key] = pt;
    if (key.startsWith('A')) sumA += pt;
    if (key.startsWith('B')) sumB += pt;
    if (key.startsWith('C')) sumC += pt;
  }

  const sumAC = sumA + sumC;

  // ─────────────────────────────────────────────────────
  // 3. 高ストレス者の判定（厚労省素点換算表方式）
  //    ① 領域B合計 ≤ 12点
  //    ② 領域B合計 ≤ 17点 かつ 領域A+C合計 ≤ 26点
  // ─────────────────────────────────────────────────────
  const isHighStress = sumB <= 12 || (sumB <= 17 && sumAC <= 26);

  // ─────────────────────────────────────────────────────
  // 4. 速報画面用データの返却
  // ─────────────────────────────────────────────────────
  return {
    isHighStress,
    summaryScores: { sumA, sumB, sumC, sumAC },
    radarChartData: {
      stressFactors: [
        evalScores.A1_quantity,
        evalScores.A2_quality,
        evalScores.A3_physical,
        evalScores.A4_interpersonal,
        evalScores.A5_environment,
        evalScores.A6_control,
        evalScores.A7_skill,
        evalScores.A8_suitability,
        evalScores.A9_reward,
      ],
      stressReactions: [
        evalScores.B1_vigor,
        evalScores.B2_irritation,
        evalScores.B3_fatigue,
        evalScores.B4_anxiety,
        evalScores.B5_depression,
        evalScores.B6_physical,
      ],
      supports: [
        evalScores.C1_boss,
        evalScores.C2_coworker,
        evalScores.C3_family,
      ],
    },
  };
}
