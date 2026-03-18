import React, { useState } from 'react';
import { questions, categories, scoringScale } from '../data/questions';

const Questionnaire = ({ onComplete }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [animating, setAnimating] = useState(false);

  const currentQuestion = questions[currentIndex];
  // Calculate progress percentage
  const progress = Math.round((currentIndex / questions.length) * 100);

  const handleAnswer = (value) => {
    if (animating) return;

    // Save answer
    const newAnswers = [...answers, { questionId: currentQuestion.id, value }];
    setAnswers(newAnswers);

    // Proceed to next or complete
    if (currentIndex < questions.length - 1) {
      setAnimating(true);
      setTimeout(() => {
        setCurrentIndex(currentIndex + 1);
        setAnimating(false);
      }, 400); // Wait for fade out animation
    } else {
      onComplete(newAnswers);
    }
  };

  const currentCategoryLabel = categories[currentQuestion.category].title;
  const currentCategoryDesc = categories[currentQuestion.category].description;
  const currentScale = scoringScale[currentQuestion.type];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flex: 1, padding: '1rem 0' }}>
      
      {/* Progress Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          <span>質問 {currentIndex + 1} / {questions.length}</span>
          <span>{progress}%</span>
        </div>
        <div style={{ width: '100%', height: '8px', background: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ 
            height: '100%', 
            width: `${progress}%`, 
            background: 'var(--primary-gradient)',
            transition: 'width 0.3s ease-in-out'
          }}></div>
        </div>
      </div>

      {/* Question Card */}
      <div className={`glass-panel ${animating ? 'fade-out' : 'animate-fade-in'}`} style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        padding: '2rem',
        minHeight: '400px',
        transition: 'opacity 0.3s'
      }}>
        
        <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
          <span style={{ 
            display: 'inline-block', 
            background: 'var(--primary-gradient)', 
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: '600',
            fontSize: '1rem',
            marginBottom: '0.5rem'
          }}>
            {currentCategoryLabel}
          </span>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{currentCategoryDesc}</p>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: '1.5rem', marginBottom: '3rem', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {currentQuestion.text}
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
          {currentScale.map((option) => (
            <button
              key={option.value}
              className="btn btn-secondary"
              style={{
                padding: '1.25rem 1rem',
                fontSize: '1rem',
                fontWeight: '500',
                borderWidth: '2px',
              }}
              onClick={() => handleAnswer(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      
    </div>
  );
};

export default Questionnaire;
