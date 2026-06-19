'use client'

import { motion } from 'framer-motion'

interface ScrollRevealProps {
  children: React.ReactNode
  delay?: number
  className?: string
  y?: number
}

export default function ScrollReveal({ children, delay = 0, className = '', y = 28 }: ScrollRevealProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{
        type: 'spring',
        stiffness: 280,
        damping: 26,
        delay,
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
