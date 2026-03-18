import React from 'react';

const StartScreen = ({ onStart }) => {
  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '3rem 2rem', textAlign: 'center', marginTop: 'auto', marginBottom: 'auto' }}>
      <h1 style={{ 
        background: 'var(--primary-gradient)', 
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        marginBottom: '1rem'
      }}>
        5分でできる<br/>職場のストレスセルフチェック
      </h1>
      
      <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '2rem', maxWidth: '500px', margin: '0 auto 2rem' }}>
        最近1ヶ月の状態について、もっともあてはまるものをお答えください。<br/>
        このチェックは、ご自身のストレス度合いに気づくための参考としてご利用ください。
      </p>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        <button 
          className="btn btn-primary" 
          onClick={onStart}
          style={{ fontSize: '1.1rem', padding: '1rem 3rem' }}
        >
          チェックを始める
        </button>
      </div>

      <p style={{ marginTop: '2rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        ※結果の判定は厚生労働省が推奨する「職業性ストレス簡易調査票」の基準を参考にしています。
      </p>
    </div>
  );
};

export default StartScreen;
