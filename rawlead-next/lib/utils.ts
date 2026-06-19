export function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime()
  if (diff < 90000) return 'только что'
  if (diff < 3600000) return Math.floor(diff / 60000) + ' мин'
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'ч'
  const d = Math.floor(diff / 86400000)
  return d === 1 ? 'вчера' : d + ' д'
}

export const SOURCE_LABEL: Record<string, string> = {
  fl: 'FL.ru',
  kwork: 'Kwork',
  youdo: 'YouDo',
  tg: 'Telegram',
  'freelance-ru': 'Freelance.ru',
  freelancejob: 'FreelanceJob',
  pchyol: 'Пчёл',
}

export const SOURCE_COLOR: Record<string, string> = {
  fl: '#00A65A',
  kwork: '#EA580C',
  youdo: '#2563EB',
  tg: '#0088CC',
}

export const NICHE_ICON: Record<string, string> = {
  dev: '</>',
  design: '✦',
  marketing: '◎',
  text: 'Aa',
}

export const DIFFICULTY_BADGES: Record<number, { badge: string; tip: string }> = {
  1: { badge: '🟢 Один вечер', tip: 'Скрипт, один файл, понятное ТЗ — вечер работы.' },
  2: { badge: '🟡 Проект', tip: 'Типовая архитектура — понятно с первого прочтения.' },
  3: { badge: '🟠 Система', tip: 'Несколько компонентов или монолит с нормальным ТЗ. Потребует время на разбор.' },
  4: { badge: '🔴 Без норм ТЗ', tip: 'Нет нормального ТЗ, «сделайте красиво» или каша в описании. Риск на тебе.' },
}
