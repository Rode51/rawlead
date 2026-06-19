import Link from 'next/link'
import { forwardRef } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  href?: string
  children: React.ReactNode
  className?: string
}

const sizes: Record<Size, string> = {
  sm: 'px-4 py-2.5 text-[12px] tracking-[0.06em]',
  md: 'px-6 py-3.5 text-[13px] tracking-[0.05em]',
  lg: 'px-8 py-4 text-[14px] tracking-[0.04em]',
}

const variants: Record<Variant, string> = {
  primary: [
    'bg-[#111010] text-white border-[#111010]',
    'hover:bg-[#E8A020] hover:text-[#111010] hover:border-[#111010]',
  ].join(' '),
  secondary: [
    'bg-transparent text-[#111010] border-[#111010]',
    'hover:bg-[#EEEDEA]',
  ].join(' '),
  ghost: 'bg-transparent text-[#111010] border-transparent underline underline-offset-4 hover:no-underline',
}

const base = 'inline-flex items-center justify-center gap-2 font-bold uppercase font-sans border-2 rounded-none transition-colors duration-100 active:scale-[0.97] cursor-pointer select-none'

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', href, children, className = '', ...props }, ref) => {
    const cls = `${base} ${sizes[size]} ${variants[variant]} ${className}`

    if (href) {
      return <Link href={href} className={cls}>{children}</Link>
    }

    return (
      <button ref={ref} className={cls} {...props}>
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
