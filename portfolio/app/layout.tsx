import type { Metadata } from "next";
import localFont from "next/font/local";
import { Barlow_Condensed, Oswald, JetBrains_Mono } from "next/font/google";
import CustomCursor from "./components/CustomCursor";
import Grain from "./components/Grain";
import SmoothScroll from "./components/SmoothScroll";
import ScrollUI from "./components/ScrollUI";
import "./globals.css";

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

const barlowCondensed = Barlow_Condensed({
  weight: ["400", "700", "900"],
  subsets: ["latin"],
  variable: "--font-barlow-condensed",
  display: "swap",
});

const oswald = Oswald({
  weight: ["400", "700"],
  subsets: ["latin", "cyrillic"],
  variable: "--font-oswald",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin", "cyrillic"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

const BASE_URL = 'https://rode51.ru'

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),

  title: {
    default: 'Rode51 — Боты, парсеры, автоматизация',
    template: '%s — Rode51',
  },
  description:
    'Строю Telegram-боты, парсеры и веб-сервисы под задачу. От идеи до продакшена — пишу, деплою, поддерживаю без посредников.',

  keywords: [
    'разработка ботов',
    'telegram bot',
    'парсер сайтов',
    'автоматизация бизнеса',
    'веб-разработка',
    'python разработчик',
    'интеграция api',
    'фриланс разработчик',
  ],

  authors: [{ name: 'Rode51', url: BASE_URL }],
  creator: 'Rode51',

  openGraph: {
    type: 'website',
    url: BASE_URL,
    siteName: 'Rode51',
    title: 'Rode51 — Боты, парсеры, автоматизация',
    description:
      'Строю Telegram-боты, парсеры и веб-сервисы под задачу. Пишу, деплою, поддерживаю — без посредников.',
    locale: 'ru_RU',
  },

  twitter: {
    card: 'summary',
    title: 'Rode51 — Боты, парсеры, автоматизация',
    description:
      'Строю Telegram-боты, парсеры и веб-сервисы под задачу. Пишу, деплою, поддерживаю — без посредников.',
    creator: '@rode_51',
  },

  robots: {
    index: true,
    follow: true,
  },

  alternates: {
    canonical: BASE_URL,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body
        className={`${geistMono.variable} ${barlowCondensed.variable} ${oswald.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <CustomCursor />
        <Grain />
        <ScrollUI />
        <SmoothScroll>
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
