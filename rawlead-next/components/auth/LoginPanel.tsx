'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { authApi } from '@/lib/api'
import { BotLoginError, startBotLoginPoll } from '@/lib/bot-login'
import { useAuth } from '@/lib/auth-context'

const TG_ICON = (
  <svg className="shrink-0" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
    <path
      fill="currentColor"
      d="M9.04 15.314l-.376 5.302c.538 0 .77-.231 1.049-.508l2.518-2.418 5.217 3.823c.957.527 1.637.251 1.898-.885l3.438-16.08.001-.001c.305-1.423-.514-1.98-1.447-1.634L1.12 9.775c-1.392.541-1.369 1.317-.236 1.667l4.913 1.533L18.9 5.48c.595-.394 1.136-.176.691.218"
    />
  </svg>
)

const PRIMARY_BTN =
  'inline-flex items-center justify-center gap-2 w-full sm:w-auto h-12 px-7 bg-[#FACC15] text-[#111010] font-display font-black text-[13px] uppercase tracking-[0.08em] border-2 border-[#111010] shadow-[4px_4px_0_#111010] hover:shadow-[6px_6px_0_#111010] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150 disabled:opacity-60 disabled:pointer-events-none'

const GHOST_BTN =
  'inline-flex items-center justify-center h-10 px-4 text-[13px] font-semibold text-[#6B6B6B] underline hover:text-[#111010] hover:no-underline transition-colors bg-transparent border-0 cursor-pointer'

type PanelPhase = 'idle' | 'loading' | 'qr' | 'error' | 'ok'
type StateTone = 'info' | 'warn' | 'error' | 'ok' | ''

function isWideScreen(): boolean {
  if (typeof window === 'undefined') return true
  return window.matchMedia('(min-width: 768px)').matches
}

function qrImageUrl(deepLink: string): string {
  return `https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=12&data=${encodeURIComponent(deepLink)}`
}

interface Props {
  variant?: 'cabinet' | 'modal'
  onSuccess?: () => void
}

export default function LoginPanel({ variant = 'cabinet', onSuccess }: Props) {
  const auth = useAuth()
  const [phase, setPhase] = useState<PanelPhase>('idle')
  const [deepLink, setDeepLink] = useState('')
  const [mobileMode, setMobileMode] = useState(false)
  const [stateTone, setStateTone] = useState<StateTone>('')
  const [stateMsg, setStateMsg] = useState('')
  const stopPollRef = useRef<(() => void) | null>(null)
  const wideRef = useRef(true)

  const stopPoll = useCallback(() => {
    stopPollRef.current?.()
    stopPollRef.current = null
  }, [])

  const setLoginState = useCallback((tone: StateTone, message: string) => {
    setStateTone(tone)
    setStateMsg(message)
  }, [])

  const hideQrPanel = useCallback(() => {
    stopPoll()
    setPhase('idle')
    setDeepLink('')
    setLoginState('', '')
  }, [setLoginState, stopPoll])

  const handleSuccess = useCallback(
    (profile: Parameters<typeof auth.login>[0], subscription: Parameters<typeof auth.login>[1]) => {
      setPhase('ok')
      setLoginState('ok', 'Вход выполнен. Загружаем кабинет…')
      auth.login(profile, subscription)
      onSuccess?.()
    },
    [auth, onSuccess, setLoginState],
  )

  const startLogin = useCallback(async () => {
    setPhase('loading')
    setLoginState('info', isWideScreen() ? 'Готовим QR-код…' : 'Откройте Telegram и нажмите Start.')
    stopPoll()
    auth.cancelBootstrap()

    try {
      const session = await authApi.botSession()
      const mobile = !isWideScreen()
      wideRef.current = !mobile
      setMobileMode(mobile)
      setDeepLink(session.deep_link)
      setPhase('qr')
      setLoginState(
        'info',
        mobile
          ? 'Откройте Telegram и нажмите Start.'
          : 'Отсканируйте QR телефоном и нажмите Start в боте.',
      )
      stopPollRef.current = startBotLoginPoll(session.auth_token, session.expires_at, {
        onWaiting: link => setDeepLink(link),
        onSuccess: handleSuccess,
        onError: message => {
          hideQrPanel()
          setPhase('error')
          setLoginState('error', message)
        },
      })
    } catch (err) {
      hideQrPanel()
      setPhase('error')
      setLoginState(
        'error',
        err instanceof BotLoginError
          ? err.message
          : 'Не удалось открыть Telegram. Попробуйте через бота ниже.',
      )
    }
  }, [auth, handleSuccess, hideQrPanel, setLoginState, stopPoll])

  useEffect(() => () => stopPoll(), [stopPoll])

  const showIdleBtn = phase === 'idle' || phase === 'error'
  const showQr = phase === 'qr' && !!deepLink
  const qrUrl = deepLink && wideRef.current && !mobileMode ? qrImageUrl(deepLink) : null

  const stateColor =
    stateTone === 'error'
      ? 'text-red-600'
      : stateTone === 'ok'
        ? 'text-[#00A65A]'
        : stateTone === 'warn'
          ? 'text-[#D97706]'
          : 'text-[#6B6B6B]'

  return (
    <div data-testid={variant === 'cabinet' ? 'cabinet-login-panel' : 'login-panel'}>
      {variant === 'cabinet' ? (
        <>
          <h1
            className="font-display font-black text-[#111010]"
            style={{ fontSize: '2rem', letterSpacing: '-0.04em', marginTop: 24, marginBottom: 12 }}
          >
            Кабинет
          </h1>
          <p className="text-[1rem] text-[#525252] leading-relaxed mb-8">
            Лента уже подбирает совпадения. Войди — посмотришь свой профиль и черновики.
          </p>
        </>
      ) : (
        <>
          <h2 className="font-black text-[18px] text-[#111010] mb-1">Войти через Telegram</h2>
          <p className="text-[13px] text-[#6B6B6B] mb-6">3 дня Premium бесплатно при первом входе</p>
        </>
      )}

      {showIdleBtn && (
        <button
          type="button"
          id="rl-cabinet-login-btn"
          data-testid="login-panel-start"
          className={PRIMARY_BTN}
          onClick={() => void startLogin()}
        >
          {TG_ICON}
          Войти через Telegram
        </button>
      )}

      {showQr && (
        <div
          id="rl-cabinet-login-qr"
          data-testid="login-panel-qr"
          className="mt-6 flex flex-col gap-4"
        >
          <p
            className={`text-[13px] text-[#6B6B6B] leading-relaxed ${mobileMode ? 'block' : 'hidden md:block'}`}
          >
            {mobileMode
              ? 'Откройте Telegram и нажмите Start. Эта страница останется открытой — кабинет войдёт сам.'
              : 'Отсканируйте камерой телефона — откроется бот, нажмите Start.'}
          </p>

          {qrUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              id="rl-cabinet-login-qr-img"
              src={qrUrl}
              alt="QR-код для входа через Telegram"
              width={260}
              height={260}
              className="hidden md:block border-2 border-[#111010] bg-white p-3"
            />
          )}

          <p
            id="rl-cabinet-login-qr-wait"
            className="text-[13px] text-[#6B6B6B] flex items-center gap-2"
          >
            <span className="animate-spin" aria-hidden="true">↺</span>
            Ждём подтверждение в Telegram…
          </p>

          {deepLink && (
            <p className="rl-cabinet-login__qr-link">
              {mobileMode ? (
                <a
                  id="rl-cabinet-login-qr-link"
                  href={deepLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${PRIMARY_BTN} md:hidden`}
                >
                  {TG_ICON}
                  Открыть Telegram
                </a>
              ) : (
                <a
                  id="rl-cabinet-login-qr-link"
                  href={deepLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${GHOST_BTN} hidden md:inline-flex`}
                >
                  Открыть ссылку на телефоне
                </a>
              )}
            </p>
          )}

          <button
            type="button"
            id="rl-cabinet-login-qr-cancel"
            data-testid="login-panel-cancel"
            className={`${GHOST_BTN} self-start`}
            onClick={hideQrPanel}
          >
            Отмена
          </button>
        </div>
      )}

      {stateMsg ? (
        <p
          id="rl-cabinet-login-state"
          role={stateTone === 'error' ? 'alert' : 'status'}
          aria-live="polite"
          className={`mt-4 text-[13px] ${stateColor}`}
        >
          {stateMsg}
        </p>
      ) : null}
    </div>
  )
}
