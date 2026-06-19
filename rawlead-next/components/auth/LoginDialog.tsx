'use client'

import LoginPanel from '@/components/auth/LoginPanel'

interface Props {
  onClose: () => void
}

export default function LoginDialog({ onClose }: Props) {
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center" data-testid="login-modal">
      <div
        data-testid="login-modal-backdrop"
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      <div
        className="relative bg-white z-10 w-full max-w-[400px] mx-4 p-8"
        style={{ border: '2px solid #111010', boxShadow: '6px 6px 0 #111010' }}
      >
        <button
          data-testid="login-modal-close"
          className="absolute top-4 right-4 text-[#6B6B6B] hover:text-[#111010] text-[18px]"
          onClick={onClose}
        >
          ✕
        </button>

        <LoginPanel variant="modal" onSuccess={onClose} />
      </div>
    </div>
  )
}
