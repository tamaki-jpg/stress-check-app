import { questions } from '../data/questions';

/**
 * Calculates scores for all categories based on user answers
 * @param {Array} answers - Array of objects { questionId, value }
 * @returns {Object} - Result object with total and category breakdown
 */
export const calculateScore = (answers) => {
  // Initialize scores
  const scores = {
    A: { total: 0, max: 0, normalized: 0 },
    B: { total: 0, max: 0, normalized: 0 },
    C: { total: 0, max: 0, normalized: 0 },
    total: 0
  };

  answers.forEach((answer) => {
    const question = questions.find(q => q.id === answer.questionId);
    if (!question) return;

    let value = answer.value;
    
    // Handle reverse scored items (e.g., "I get along with coworkers" -> high score = low stress)
    // Values are 1, 2, 3, 4. Reverse becomes 5 - value.
    if (question.reverse) {
      value = 5 - value;
    }

    const cat = question.category;
    scores[cat].total += value;
    scores[cat].max += 4; // Max score per question is 4
  });

  // Calculate normalized percentage (0-100) where 100 is maximum stress
  ['A', 'B', 'C'].forEach(cat => {
    if (scores[cat].max > 0) {
      scores[cat].normalized = (scores[cat].total / scores[cat].max) * 100;
      scores.total += scores[cat].normalized;
    }
  });

  // Average overall stress score
  scores.overall = scores.total / 3;

  // Determine stress level string
  let level = 'Low';
  let message = '現在のストレスレベルは低く、良好な状態です。';
  let color = '#10b981'; // Tailwind Emerald 500

  // Standard threshold logic (simplified for this app)
  if (scores.B.normalized > 77 || (scores.A.normalized + scores.C.normalized > 152 && scores.B.normalized > 63)) {
     level = 'High';
     message = '高ストレス状態です。医師や産業医への相談をおすすめします。';
     color = '#ef4444'; // Tailwind Red 500
  } else if (scores.overall > 60) {
     level = 'Moderate';
     message = '中程度のストレスを感じています。適度な休息を心がけましょう。';
     color = '#f59e0b'; // Tailwind Amber 500
  }

  return {
    breakdown: scores,
    evaluation: {
      level,
      message,
      color
    }
  };
};
