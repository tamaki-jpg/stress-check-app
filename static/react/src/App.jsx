import React, { useState } from 'react';
import StressProfileResult from './StressProfileResult.jsx';
import { calculateStressProfile } from './calculateStressProfile.js';

// ─────────────────────────────────────────────────────────────
// 表示テスト用ダミー回答データ（q1〜q57、全て中程度の値）
//
// ※ 本番では Flask の /api/submit レスポンスや
//    URL パラメータからこのデータを受け取って差し替えてください。
// ─────────────────────────────────────────────────────────────
const DUMMY_ANSWERS_NORMAL = {
  // ── 領域A (q1〜q17): 仕事のストレス要因 ──────────────
  q1: 2, q2: 2, q3: 2,   // 量的負担（低め＝ストレス少）
  q4: 2, q5: 2, q6: 2,   // 質的負担
  q7: 2,                  // 身体的負担
  q8: 3, q9: 3, q10: 3,  // コントロール（高め＝自律性あり）
  q11: 3,                 // 技術の活用
  q12: 2, q13: 2, q14: 2,// 対人関係
  q15: 2,                 // 職場環境
  q16: 3, q17: 3,         // 適合性・働きがい

  // ── 領域B (q18〜q46): 心身のストレス反応 ──────────────
  q18: 3, q19: 3, q20: 3, // 活気（高め＝元気）
  q21: 2, q22: 2, q23: 2, // イライラ感（低め＝少ない）
  q24: 2, q25: 2, q26: 2, // 疲労感
  q27: 2, q28: 2, q29: 2, // 不安感
  q30: 1, q31: 1, q32: 1, q33: 1, q34: 1, q35: 1, // 抑うつ感（低め）
  q36: 1, q37: 1, q38: 1, q39: 1, q40: 1,
  q41: 1, q42: 1, q43: 1, q44: 1, q45: 1, q46: 1, // 身体愁訴

  // ── 領域C (q47〜q55): 周囲のサポート ─────────────────
  q47: 2, q48: 2, q49: 1, // 気軽に話せる（低め＝サポートあり）
  q50: 2, q51: 2, q52: 1, // 頼りになる
  q53: 2, q54: 2, q55: 1, // 個人的な問題を聞いてくれる

  // ── 領域D (q56〜q57) ─────────────────────────────────
  q56: 2, q57: 2,
};

// 高ストレス判定が出るダミーデータ（比較テスト用）
const DUMMY_ANSWERS_HIGH_STRESS = {
  q1: 4, q2: 4, q3: 4,
  q4: 4, q5: 4, q6: 4,
  q7: 4,
  q8: 1, q9: 1, q10: 1,
  q11: 1,
  q12: 4, q13: 4, q14: 1,
  q15: 4,
  q16: 1, q17: 1,
  q18: 1, q19: 1, q20: 1, // 活気なし
  q21: 4, q22: 4, q23: 4,
  q24: 4, q25: 4, q26: 4,
  q27: 4, q28: 4, q29: 4,
  q30: 4, q31: 4, q32: 4, q33: 4, q34: 4, q35: 4,
  q36: 4, q37: 4, q38: 4, q39: 4, q40: 4,
  q41: 4, q42: 4, q43: 4, q44: 4, q45: 4, q46: 4,
  q47: 4, q48: 4, q49: 4,
  q50: 4, q51: 4, q52: 4,
  q53: 4, q54: 4, q55: 4,
  q56: 2, q57: 2,
};

export default function App() {
  const [useHighStress, setUseHighStress] = useState(false);

  const answers = useHighStress ? DUMMY_ANSWERS_HIGH_STRESS : DUMMY_ANSWERS_NORMAL;
  const gender  = 'male'; // 'male' | 'female'

  const result = calculateStressProfile(answers, gender);

  return (
    <div>
      {/* ── 切り替えスイッチ（開発確認用） ── */}
      <div style={{
        position: 'fixed', top: 12, right: 16, zIndex: 9999,
        display: 'flex', alignItems: 'center', gap: 10,
        background: 'white', border: '1px solid #d1d5db',
        borderRadius: 8, padding: '6px 14px', boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
        fontSize: 13, fontFamily: 'sans-serif',
      }}>
        <span style={{ color: '#6b7280' }}>表示テスト：</span>
        <button
          onClick={() => setUseHighStress(false)}
          style={{
            padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
            background: !useHighStress ? '#559018' : '#e5e7eb',
            color: !useHighStress ? 'white' : '#374151', fontWeight: 600, fontSize: 12,
          }}
        >通常</button>
        <button
          onClick={() => setUseHighStress(true)}
          style={{
            padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
            background: useHighStress ? '#dc2626' : '#e5e7eb',
            color: useHighStress ? 'white' : '#374151', fontWeight: 600, fontSize: 12,
          }}
        >高ストレス</button>
      </div>

      {/* ── 結果コンポーネント本体 ── */}
      <StressProfileResult
        isHighStress={result.isHighStress}
        summaryScores={result.summaryScores}
        radarChartData={result.radarChartData}
      />
    </div>
  );
}
