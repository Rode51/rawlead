'use client'

import { useEffect, useState } from 'react'
import { getToken } from '@/lib/api'
import type { UserProfile } from '@/lib/types'
import {
  displayInitial,
  fetchAvatarBlobUrl,
  isBrokenWpAvatarUrl,
  resolveAvatarSrc,
} from '@/lib/user-meta'

interface Props {
  profile: UserProfile | null | undefined
  size?: number
  className?: string
  style?: React.CSSProperties
}

export default function UserAvatar({ profile, size = 36, className = '', style }: Props) {
  const [src, setSrc] = useState('')
  const letter = displayInitial(profile)

  useEffect(() => {
    let blobUrl: string | null = null
    let cancelled = false

    async function load() {
      const token = getToken()
      const next = resolveAvatarSrc(token, profile ?? null)
      if (!next) {
        setSrc('')
        return
      }
      if (next.includes('/me/avatar')) {
        if (!token) {
          setSrc('')
          return
        }
        blobUrl = await fetchAvatarBlobUrl(token)
        if (!cancelled) setSrc(blobUrl || '')
        return
      }
      if (!cancelled) setSrc(next)
    }

    void load()
    return () => {
      cancelled = true
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
  }, [profile?.user_id, profile?.avatar_url, profile?.has_avatar, profile?.tg_user_id])

  function onImgError() {
    const token = getToken()
    const direct = (profile?.avatar_url || '').trim()
    if (!token || !direct || isBrokenWpAvatarUrl(direct)) {
      setSrc('')
      return
    }
    void fetchAvatarBlobUrl(token).then(url => setSrc(url || ''))
  }

  return (
    <span
      className={`inline-flex items-center justify-center shrink-0 overflow-hidden font-black ${className}`}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        border: '2px solid #111010',
        background: '#FACC15',
        fontSize: Math.round(size * 0.38),
        ...style,
      }}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt=""
          width={size}
          height={size}
          onError={onImgError}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <span>{letter}</span>
      )}
    </span>
  )
}
