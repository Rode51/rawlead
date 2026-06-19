'use client'

import { motion } from 'framer-motion'

export default function Manifest() {
  return (
    <section className="bg-rl-inverse text-rl-page py-24 md:py-32 border-y-2 border-rl-inverse overflow-hidden">
      <div
        className="mx-auto px-6 text-center"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 280, damping: 26 }}
          viewport={{ once: true, margin: '-80px' }}
          className="font-display font-black text-3xl md:text-5xl lg:text-6xl tracking-tight leading-tight text-white"
        >
          Перестань мониторить.
          <br />
          Начни откликаться.
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 280, damping: 26, delay: 0.12 }}
          viewport={{ once: true, margin: '-80px' }}
          className="mt-6 text-gray-400 font-sans text-lg md:text-xl max-w-xl mx-auto"
        >
          Один поток вместо десяти вкладок.
        </motion.p>
      </div>
    </section>
  )
}
