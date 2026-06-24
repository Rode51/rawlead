import type { SiteContent } from './ru'

export const enProjects = {
  label:    '/ PROJECTS',
  subtitle: 'Finds leads. Drafts replies. Runs itself.',
  desc:     'RawLead monitors freelance platforms so you don\'t have to: collects orders, ranks them by skill match, and drafts a reply for every suitable lead. Live in production, processing orders in real time.',
  metrics: [
    { val: '7',    label: 'platforms' },
    { val: '~50s', label: 'to appear in feed' },
    { val: '3',    label: 'AI analysis layers' },
    { val: '24/7', label: 'in production' },
  ],
  inProd:     '/ IN PROD',
  whatInside: '— WHAT\'S INSIDE',
  open:       '→ OPEN',
  close:      '× CLOSE',
  cases: [
    {
      title:   'PARSER',
      preview: '7 platforms · ~50s cycle',
      stack:   ['7 platforms simultaneously', 'anti-bot bypass', '~50s update cycle', 'dedup and filtering'],
      body:    'The system monitors FL.ru, Kwork, YouDo and Telegram channels on its own — without you. A new order appears in the feed within seconds of being posted. No more manual searching.',
    },
    {
      title:   'AI FILTER',
      preview: '3 layers · draft per match',
      stack:   ['three analysis layers', 'skill compatibility scoring', 'reply draft per match', 'AI judge controls quality'],
      body:    'AI reads each order and scores how well it fits your stack. On a match — it drafts a reply: not a template, but text tailored to that specific request. You spend a minute instead of fifteen.',
    },
    {
      title:   'TG BOTS',
      preview: 'login without forms · alerts',
      stack:   ['Telegram login — no forms', 'instant match notification', 'alert if system goes down', 'runs 24/7'],
      body:    'One-click Telegram auth — no passwords. New matching order — instant notification in the messenger. If the system goes down — you get an alert, it doesn\'t stay silent.',
    },
    {
      title:   'INTERFACE',
      preview: 'feed · cabinet · match %',
      stack:   ['open feed without registration', 'personal cabinet with replies', 'skill setup per niche', 'sorted by match %'],
      body:    'Open feed with orders sorted by stack compatibility — viewable without registration. In the cabinet: reply history, skill settings across 4 niches, Telegram-based profile.',
    },
  ],
}

export const en: SiteContent = {
  hero: {
    role:      'FULL-STACK DEVELOPER · BOTS · PARSERS · AUTOMATION · WEBSITES',
    line1:     'I build bots, parsers, websites and automation.',
    line2:     'I code, deploy, support — no middlemen.',
    cta:       '→ Message on Telegram',
    available: 'AVAILABLE FOR PROJECTS',
  },
  tagline: 'From idea to production.',
  services: {
    label: '/ WHAT I DO',
    items: [
      { title: 'BOT',        body: 'Telegram bot for taking orders — no app or forms needed, runs 24/7' },
      { title: 'PARSER',     body: 'Monitor sites and platforms — new orders or prices straight to Telegram' },
      { title: 'AUTOMATION', body: 'Remove manual work — scripts run instead of humans on a schedule' },
      { title: 'INTEGRATION', body: 'Connect CRM, Telegram, Sheets — data flows between services automatically' },
      { title: 'LANDING',    body: 'Landing page in 3–5 days — form, analytics, deployed to your domain' },
      { title: 'WEBSITE',    body: 'Website from design to production — Next.js, TypeScript, SEO-ready' },
    ],
  },
  whyMe: {
    label: '/ WHY ME',
    items: [
      { title: 'FIXED PRICE',       body: 'I quote the cost before starting. No "just a bit more" mid-project.' },
      { title: 'PAY AFTER',         body: 'You verify everything works as needed — then you pay.' },
      { title: 'REMOTE',            body: 'I work from anywhere. No office, no pointless calls.' },
      { title: 'SUPPORT',           body: "I stay available after delivery. If something breaks — I'll fix it." },
    ],
  },
  process: {
    label: '/ HOW WE WORK',
    steps: [
      { num: '01', title: 'You describe the task',  body: 'No briefs or specs. Write in Telegram what you need and why — we figure out the details together.' },
      { num: '02', title: 'You get a plan',          body: 'What I build, how long it takes, what you get. I name the price before starting — no surprises.' },
      { num: '03', title: 'You take the result',     body: 'Pay after review — verify it works, then pay. Deploy, docs, ongoing support.' },
    ],
    note: 'Usually from first message to a working bot or landing page — 3–5 days.',
  },
  faq: {
    label: '/ FAQ',
    items: [
      { q: 'How fast?',             a: 'Bot or landing page — 3–5 days. Parser and automation — depends on the task. I give a timeline before starting.' },
      { q: 'Do I need a spec?',     a: 'No. Just tell me in plain words what you need and why — we work out the details together.' },
      { q: "What if I don't like it?", a: 'Payment only after review. If it works for you — you pay. If not — you don\'t.' },
      { q: 'How does remote work?', a: 'Telegram. No mandatory calls. Write when convenient — I respond within 24h.' },
      { q: 'How do I pay?',        a: 'Bank transfer (RUB), via freelance platform (FL.ru, Kwork, YouDo), or crypto — USDT/USDC (TRC-20/ERC-20). You pay after verifying the result.' },
    ],
  },
  footer: {
    label:    '/ CONTACT',
    headline: 'Got a task',
    sub1:     'Tell me about it on Telegram — I\'ll reply within 24h.',
    sub2:     'Fixed price, no surprises.',
    cta:      '→ Message on Telegram',
    handle:   '@rode_51',
    city:     'MOSCOW',
  },
  ticker: 'Taking projects  ·  Remote  ·  Reply ~24h  ·  Full-stack  ·  Prod  ·  @rode_51  ·  ',
  nav: { ru: 'RU', en: 'EN' },
}
