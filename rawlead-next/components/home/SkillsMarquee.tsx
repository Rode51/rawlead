'use client'

import { motion } from 'framer-motion'

const SKILLS = [
  'Python', 'WordPress', 'React', 'Figma', 'SEO',
  'Laravel', 'Telegram Bot', 'UI/UX', 'Копирайтинг',
  'Node.js', 'PHP', 'Таргет',
]

/** Black skills strip — visual divider between yellow Hero and gray LivePreview. */
export default function SkillsMarquee() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 1.1, duration: 0.6 }}
      className="overflow-hidden border-y-2 border-[#111010] bg-[#111010] py-3"
      aria-label="Навыки"
    >
      <div
        className="marquee-run"
        style={{ '--marquee-dur': '22s' } as React.CSSProperties}
      >
        {[...SKILLS, ...SKILLS, ...SKILLS].map((skill, i) => (
          <span
            key={i}
            className="inline-flex items-center shrink-0 mx-4 font-display font-black text-xs uppercase tracking-[0.1em] text-[#FACC15] px-3 py-1 border border-[#FACC15]/40"
          >
            {skill}
          </span>
        ))}
      </div>
    </motion.div>
  )
}
