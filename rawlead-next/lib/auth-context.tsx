'use client'

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { clearToken, getToken, meApi } from './api'
import { completeAuthAfterToken } from './auth-session'
import { mergeGuestSkillsAfterAuth } from './guest-skills'
import { readUserMeta, saveUserMeta } from './user-meta'
import type { SubscriptionStatus, UserProfile } from './types'

export type FeedTier = 'pending' | 'anon' | 'free' | 'expired_trial' | 'premium'

interface AuthContextValue {
  status: 'pending' | 'anon' | 'auth'
  profile: UserProfile | null
  subscription: SubscriptionStatus | null
  tags: string[]
  feedTier: FeedTier
  hasUserSkills: boolean
  login: (profile: UserProfile, subscription: SubscriptionStatus) => void
  logout: () => void
  cancelBootstrap: () => void
  refreshTags: () => Promise<void>
  refreshSubscription: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

function deriveTier(
  status: 'pending' | 'anon' | 'auth',
  subscription: SubscriptionStatus | null,
): FeedTier {
  if (status === 'pending' || status === 'anon') return 'anon'
  if (!subscription) return 'free'
  if (subscription.effective_access) return 'premium'
  const st = subscription.status || ''
  if (st === 'expired' || st === 'paused' || subscription.trial_used_at) return 'expired_trial'
  return 'free'
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<'pending' | 'anon' | 'auth'>('pending')
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null)
  const [tags, setTags] = useState<string[]>([])
  const sessionEpochRef = useRef(0)

  const feedTier = deriveTier(status, subscription)
  const hasUserSkills = tags.length > 0

  const cancelBootstrap = useCallback(() => {
    sessionEpochRef.current += 1
    if (process.env.NODE_ENV !== 'production') {
      console.info('[auth] bootstrap cancelled, epoch=', sessionEpochRef.current)
    }
  }, [])

  const refreshTags = useCallback(async () => {
    try {
      const data = await meApi.tags()
      setTags(data.tags || [])
    } catch {
      // silent
    }
  }, [])

  const refreshSubscription = useCallback(async () => {
    try {
      const data = await meApi.subscription()
      setSubscription(data)
    } catch {
      // silent
    }
  }, [])

  // WP ensureProfileFromServer — refresh /me while token exists; stay pending until resolve/reject
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setStatus('anon')
      return
    }

    const cached = readUserMeta()
    if (cached?.username || cached?.first_name) {
      setProfile(prev => prev ?? ({
        user_id: '',
        tg_user_id: 0,
        username: cached.username || '',
        first_name: cached.first_name || '',
        avatar_url: cached.avatar_url || '',
        has_avatar: !!cached.has_avatar,
        can_ops_admin: !!cached.can_ops_admin,
      }))
    }

    let cancelled = false
    const bootEpoch = sessionEpochRef.current

    completeAuthAfterToken()
      .then(async ({ profile: prof, subscription: sub }) => {
        if (cancelled || sessionEpochRef.current !== bootEpoch) {
          if (process.env.NODE_ENV !== 'production' && sessionEpochRef.current !== bootEpoch) {
            console.info('[auth] bootstrap then skipped, epoch', bootEpoch, '→', sessionEpochRef.current)
          }
          return
        }
        setProfile(prof)
        setSubscription(sub)
        setStatus('auth')
        await mergeGuestSkillsAfterAuth()
        return meApi.tags()
      })
      .then(tagsData => {
        if (cancelled || sessionEpochRef.current !== bootEpoch || !tagsData) return
        setTags(tagsData.tags || [])
      })
      .catch(() => {
        if (cancelled || sessionEpochRef.current !== bootEpoch) {
          if (process.env.NODE_ENV !== 'production' && sessionEpochRef.current !== bootEpoch) {
            console.info('[auth] bootstrap catch skipped, epoch', bootEpoch, '→', sessionEpochRef.current)
          }
          return
        }
        clearToken()
        setProfile(null)
        setSubscription(null)
        setTags([])
        setStatus('anon')
      })

    return () => { cancelled = true }
  }, [])

  // Header skeleton cap — do not stay pending forever
  useEffect(() => {
    if (status !== 'pending') return
    const id = setTimeout(() => {
      setStatus(s => (s === 'pending' ? 'anon' : s))
    }, 8000)
    return () => clearTimeout(id)
  }, [status])

  useEffect(() => {
    function onTagsImported() {
      refreshTags()
    }
    window.addEventListener('rawlead-tags-imported', onTagsImported)
    return () => window.removeEventListener('rawlead-tags-imported', onTagsImported)
  }, [refreshTags])

  const login = useCallback((prof: UserProfile, sub: SubscriptionStatus) => {
    if (process.env.NODE_ENV !== 'production') {
      console.info('[auth] login', prof.username || prof.first_name || prof.user_id)
    }
    saveUserMeta(prof)
    setProfile(prof)
    setSubscription(sub)
    setStatus('auth')
    meApi.tags().then(d => setTags(d.tags || [])).catch(() => {})
  }, [])

  const logout = useCallback(() => {
    cancelBootstrap()
    clearToken()
    setProfile(null)
    setSubscription(null)
    setTags([])
    setStatus('anon')
  }, [cancelBootstrap])

  return (
    <AuthContext.Provider value={{
      status, profile, subscription, tags,
      feedTier, hasUserSkills,
      login, logout, cancelBootstrap, refreshTags, refreshSubscription,
    }}>
      {children}
    </AuthContext.Provider>
  )
}
