'use client'

import { useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { metrikaGoal, metrikaTrialLoginOnce } from '@/lib/metrika'

export default function MetrikaGoals() {
  const { status, subscription } = useAuth()
  const loginTrackedRef = useRef(false)

  useEffect(() => {
    function onQuizComplete() {
      metrikaGoal('rl_quiz_complete')
    }
    window.addEventListener('rawlead-quiz-complete', onQuizComplete)
    return () => window.removeEventListener('rawlead-quiz-complete', onQuizComplete)
  }, [])

  useEffect(() => {
    if (status !== 'auth' || loginTrackedRef.current) return
    loginTrackedRef.current = true
    metrikaGoal('tg_login')
  }, [status])

  useEffect(() => {
    if (status !== 'auth') return
    metrikaTrialLoginOnce(subscription)
  }, [status, subscription])

  return null
}
