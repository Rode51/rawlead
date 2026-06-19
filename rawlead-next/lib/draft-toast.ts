const TOAST_EVENT = 'rawlead-draft-toast'

export function showDraftToast(message: string) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(TOAST_EVENT, { detail: message }))
}

export const DRAFT_TOAST_EVENT = TOAST_EVENT
