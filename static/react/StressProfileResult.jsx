import React from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, Legend,
} from 'recharts';

// ─────────────────────────────────────────────
// 1. レーダーチャート 単体コンポーネント
// ─────────────────────────────────────────────
const MHLW_GREEN  = '#559018';
const MHLW_FILL   = 'rgba(85,144,24,0.25)';
const WARN_RED    = '#dc2626';
const WARN_FILL   = 'rgba(220,38,38,0.20)';

function StressRadarChart({ title, data, color, fillColor }) {
  return (
    <div style={styles.chartCard}>
      <h3 style={styles.chartTitle}>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
          <PolarGrid stroke="#d1d5db" />
          {/* 目盛りラベル（軸名）を外側に表示 */}
          <PolarAngleAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#374151', fontFamily: 'sans-serif' }}
          />
          {/*
            domain を [1, 5] にすることで：
            ・中心 = 1点（高ストレス / 悪い状態）
            ・外周 = 5点（低ストレス / 良い状態）
          */}
          <PolarRadiusAxis
            domain={[1, 5]}
            tickCount={5}
            tick={{ fontSize: 9, fill: '#9ca3af' }}
            axisLine={false}
          />
          <Radar
            name="評価点"
            dataKey="value"
            stroke={color}
            fill={fillColor}
            strokeWidth={2}
            dot={{ r: 3, fill: color }}
          />
          <Tooltip
            formatter={(v) => [`${v} 点`, '評価点']}
            contentStyle={{ fontSize: 12, borderRadius: 6 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─────────────────────────────────────────────
// 2. サマリースコア 表コンポーネント
// ─────────────────────────────────────────────
function SummaryTable({ summaryScores, isHighStress }) {
  const rows = [
    {
      label: '領域A　仕事のストレス要因',
      key: 'sumA',
      range: '9〜45点',
      note: '点が高いほど良好',
    },
    {
      label: '領域B　心身のストレス反応',
      key: 'sumB',
      range: '6〜30点',
      note: '点が高いほど良好',
      threshold: isHighStress,
    },
    {
      label: '領域C　周囲のサポート',
      key: 'sumC',
      range: '3〜15点',
      note: '点が高いほどサポートが豊富',
    },
    {
      label: '領域A＋C　合計',
      key: 'sumAC',
      range: '12〜60点',
      note: '高ストレス判定の補助指標',
    },
  ];

  return (
    <div style={styles.tableWrap}>
      <h3 style={styles.sectionTitle}>詳細スコア</h3>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={{ ...styles.th, textAlign: 'left' }}>領域</th>
            <th style={styles.th}>得点</th>
            <th style={styles.th}>範囲</th>
            <th style={{ ...styles.th, textAlign: 'left' }}>補足</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={r.key}
              style={{
                background: i % 2 === 0 ? '#f9fafb' : 'white',
              }}
            >
              <td style={styles.td}>{r.label}</td>
              <td style={{ ...styles.td, textAlign: 'center', fontWeight: 700, color: MHLW_GREEN }}>
                {summaryScores[r.key]}
              </td>
              <td style={{ ...styles.td, textAlign: 'center', color: '#6b7280', fontSize: 12 }}>
                {r.range}
              </td>
              <td style={{ ...styles.td, fontSize: 12, color: '#6b7280' }}>{r.note}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 高ストレス判定の基準を補足表示 */}
      <div style={styles.criteriaBox}>
        <span style={styles.criteriaLabel}>判定基準：</span>
        <span>
          ①領域B ≤ 12点、または ②領域B ≤ 17点 かつ 領域A＋C ≤ 26点
        </span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// 3. メインコンポーネント（外部公開）
// ─────────────────────────────────────────────

/**
 * @param {Object} props
 * @param {boolean}  props.isHighStress     - 高ストレス判定フラグ
 * @param {Object}   props.summaryScores    - { sumA, sumB, sumC, sumAC }
 * @param {Object}   props.radarChartData   - { stressFactors[], stressReactions[], supports[] }
 */
export default function StressProfileResult({ isHighStress, summaryScores, radarChartData }) {
  // ── レーダーチャート用データ変換 ──────────────────
  const factorData = [
    { label: '量的負担',   value: radarChartData.stressFactors[0] },
    { label: '質的負担',   value: radarChartData.stressFactors[1] },
    { label: '身体的負担', value: radarChartData.stressFactors[2] },
    { label: '対人関係',   value: radarChartData.stressFactors[3] },
    { label: '職場環境',   value: radarChartData.stressFactors[4] },
    { label: 'コントロール', value: radarChartData.stressFactors[5] },
    { label: '技術の活用', value: radarChartData.stressFactors[6] },
    { label: '適合性',     value: radarChartData.stressFactors[7] },
    { label: '働きがい',   value: radarChartData.stressFactors[8] },
  ];

  const reactionData = [
    { label: '活気',     value: radarChartData.stressReactions[0] },
    { label: 'イライラ感', value: radarChartData.stressReactions[1] },
    { label: '疲労感',   value: radarChartData.stressReactions[2] },
    { label: '不安感',   value: radarChartData.stressReactions[3] },
    { label: '抑うつ感', value: radarChartData.stressReactions[4] },
    { label: '身体愁訴', value: radarChartData.stressReactions[5] },
  ];

  const supportData = [
    { label: '上司サポート',       value: radarChartData.supports[0] },
    { label: '同僚サポート',       value: radarChartData.supports[1] },
    { label: '家族・友人サポート', value: radarChartData.supports[2] },
  ];

  // レーダーの色：高ストレスは赤、通常は緑
  const radarColor    = isHighStress ? WARN_RED   : MHLW_GREEN;
  const radarFill     = isHighStress ? WARN_FILL  : MHLW_FILL;

  return (
    <div style={styles.wrapper}>

      {/* ── ページタイトル ── */}
      <div style={styles.pageHeader}>
        <h2 style={styles.pageTitle}>ストレスプロフィール（速報）</h2>
        <p style={styles.pageSubtitle}>
          ※ この結果は目安です。詳細は産業医・保健師にご相談ください。
        </p>
      </div>

      {/* ── 判定バナー ── */}
      {isHighStress ? (
        <div style={{ ...styles.banner, ...styles.bannerHigh }}>
          <span style={styles.bannerIcon}>⚠️</span>
          <div>
            <div style={styles.bannerHeading}>高ストレス者に該当します</div>
            <div style={styles.bannerBody}>
              現在の結果から、ストレスが高い状態にあると考えられます。
              産業医との面接指導をご検討ください。
              申し出は任意であり、結果は本人の同意なく事業者に通知されません。
            </div>
          </div>
        </div>
      ) : (
        <div style={{ ...styles.banner, ...styles.bannerOk }}>
          <span style={styles.bannerIcon}>✅</span>
          <div>
            <div style={styles.bannerHeading}>ストレス状態は概ね良好です</div>
            <div style={styles.bannerBody}>
              現在のストレス状態に特に大きな問題は見られません。
              引き続きセルフケアを心がけましょう。
            </div>
          </div>
        </div>
      )}

      {/* ── 3つのレーダーチャート ── */}
      <div style={styles.chartsRow}>
        <StressRadarChart
          title="① 仕事のストレス要因"
          data={factorData}
          color={radarColor}
          fillColor={radarFill}
        />
        <StressRadarChart
          title="② 心身のストレス反応"
          data={reactionData}
          color={radarColor}
          fillColor={radarFill}
        />
        <StressRadarChart
          title="③ 周囲のサポート"
          data={supportData}
          color={radarColor}
          fillColor={radarFill}
        />
      </div>

      {/* スケール凡例 */}
      <div style={styles.scaleLegend}>
        <span style={styles.scaleBadge}>← 中心 = 1点（高ストレス）</span>
        <span style={{ ...styles.scaleBadge, background: '#f0f5e8', color: MHLW_GREEN }}>
          外周 = 5点（良好）→
        </span>
      </div>

      {/* ── 詳細スコア表 ── */}
      <SummaryTable summaryScores={summaryScores} isHighStress={isHighStress} />

    </div>
  );
}

// ─────────────────────────────────────────────
// 4. スタイル定義（CSS-in-JS）
// ─────────────────────────────────────────────
const styles = {
  wrapper: {
    fontFamily: "'Noto Sans JP', 'Helvetica Neue', sans-serif",
    maxWidth: 1100,
    margin: '0 auto',
    padding: '24px 16px 60px',
    background: '#f2f5ee',
    minHeight: '100vh',
  },
  pageHeader: {
    marginBottom: 20,
  },
  pageTitle: {
    fontSize: 22,
    fontWeight: 700,
    color: '#3d6e0a',
    marginBottom: 4,
  },
  pageSubtitle: {
    fontSize: 12,
    color: '#6b7280',
  },

  // ── バナー ──
  banner: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 16,
    padding: '16px 20px',
    borderRadius: 10,
    marginBottom: 24,
    borderWidth: 1,
    borderStyle: 'solid',
  },
  bannerHigh: {
    background: '#fef2f2',
    borderColor: '#fca5a5',
  },
  bannerOk: {
    background: '#f0fdf4',
    borderColor: '#86efac',
  },
  bannerIcon: {
    fontSize: 28,
    flexShrink: 0,
    marginTop: 2,
  },
  bannerHeading: {
    fontSize: 16,
    fontWeight: 700,
    marginBottom: 4,
    color: '#1f2937',
  },
  bannerBody: {
    fontSize: 13,
    color: '#374151',
    lineHeight: 1.7,
  },

  // ── チャートエリア ──
  chartsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 16,
    marginBottom: 12,
  },
  chartCard: {
    background: 'white',
    borderRadius: 10,
    padding: '16px 8px 8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
  },
  chartTitle: {
    fontSize: 13,
    fontWeight: 700,
    color: '#3d6e0a',
    textAlign: 'center',
    marginBottom: 4,
    letterSpacing: 0.3,
  },

  // スケール凡例
  scaleLegend: {
    display: 'flex',
    justifyContent: 'center',
    gap: 16,
    marginBottom: 24,
  },
  scaleBadge: {
    fontSize: 11,
    padding: '4px 12px',
    borderRadius: 20,
    background: '#fef2f2',
    color: '#dc2626',
    fontWeight: 600,
  },

  // ── テーブル ──
  tableWrap: {
    background: 'white',
    borderRadius: 10,
    padding: '20px 24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: '#3d6e0a',
    marginBottom: 12,
    paddingBottom: 6,
    borderBottom: '2px solid #8cc030',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 13,
  },
  th: {
    padding: '10px 12px',
    background: '#3d6e0a',
    color: 'white',
    fontWeight: 600,
    fontSize: 12,
    textAlign: 'center',
  },
  td: {
    padding: '10px 12px',
    borderBottom: '1px solid #e5e7eb',
  },
  criteriaBox: {
    marginTop: 12,
    padding: '8px 12px',
    background: '#f9fafb',
    borderRadius: 6,
    fontSize: 11,
    color: '#6b7280',
    borderLeft: '3px solid #d1d5db',
  },
  criteriaLabel: {
    fontWeight: 700,
    color: '#374151',
    marginRight: 6,
  },
};
