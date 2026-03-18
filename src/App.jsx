import { useState } from 'react'
import StartScreen from './components/StartScreen'
import Questionnaire from './components/Questionnaire'
import ResultSection from './components/ResultSection'
import './App.css'

function App() {
  // Screen states: 'start', 'questionnaire', 'result'
  const [currentScreen, setCurrentScreen] = useState('start')
  
  // Store user's answers. Array of { questionId, value }
  const [answers, setAnswers] = useState([])

  // Handler to start the questionnaire
  const handleStart = () => {
    setCurrentScreen('questionnaire')
  }

  // Handler to complete the questionnaire and show results
  const handleComplete = (finalAnswers) => {
    setAnswers(finalAnswers)
    setCurrentScreen('result')
  }

  // Handler to restart the process
  const handleRestart = () => {
    setAnswers([])
    setCurrentScreen('start')
  }

  return (
    <div className="container">
      {currentScreen === 'start' && (
        <StartScreen onStart={handleStart} />
      )}
      
      {currentScreen === 'questionnaire' && (
        <Questionnaire onComplete={handleComplete} />
      )}
      
      {currentScreen === 'result' && (
        <ResultSection answers={answers} onRestart={handleRestart} />
      )}
    </div>
  )
}

export default App
