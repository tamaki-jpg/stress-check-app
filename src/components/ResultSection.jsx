import React, { useMemo } from 'react';
import { calculateScore } from '../utils/scoring';

const ResultSection = ({ answers, onRestart }) => {
  // calculate score only once when component mounts
  const result = useMemo(() => calculateScore(answers), [answers]);
  const { breakdown, evaluation } = result;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '3rem 2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Header and Level Result */}
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>診断結果</h2>
        
        <div style={{ 
          background: 'rgba(255,255,255,0.5)',
          border: `2px solid ${evaluation.color}`,
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: evaluation.color, fontSize: '1.5rem', marginBottom: '1rem' }}>
            ストレスレベル: {evaluation.level === 'High' ? '高' : evaluation.level === 'Moderate' ? '中' : '低'}
          </h3>
          <p style={{ fontSize: '1.1rem', fontWeight: '500' }}>
            {evaluation.message}
          </p>
        </div>
      </div>

      {/* Breakdown Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
        
        <MetricCard 
          title="仕事のストレス要因" 
          score={breakdown.A.normalized} 
          desc="仕事の量・コントロール度等" 
        />
        
        <MetricCard 
          title="心身のストレス反応" 
          score={breakdown.B.normalized} 
          desc="疲労感・不安感等" 
        />
        
        <MetricCard 
          title="周囲のサポート" 
          score={breakdown.C.normalized} 
          desc="上司や同僚の支援" 
        />

      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
        <button 
          className="btn btn-secondary" 
          onClick={onRestart}
          style={{ padding: '0.75rem 2rem' }}
        >
          もう一度やり直す
        </button>
      </div>

    </div>
  );
};

// Helper component for individual metrics
const MetricCard = ({ title, score, desc }) => {
  const roundedScore = Math.round(score);
  // Higher score = more stress. We'll color-code the bar slightly based on this.
  const barColor = roundedScore > 75 ? '#ef4444' : roundedScore > 50 ? '#f59e0b' : '#10b981';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.4)',
      borderRadius: '12px',
      padding: '1.5rem',
      border: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h4 style={{ fontSize: '1rem', color: 'var(--text-main)', marginBottom: '0.25rem' }}>{title}</h4>
      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>{desc}</p>
      
      <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ flex: 1, height: '8px', background: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ 
            height: '100%', 
            width: `${roundedScore}%`, 
            background: barColor,
            transition: 'width 1s ease-out'
          }}></div>
        </div>
        <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{roundedScore}</span>
      </div>
    </div>
  );
};

export default ResultSection;
