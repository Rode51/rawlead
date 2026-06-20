const DEFAULT_LOOP =
  "Принимаю проекты  ·  Remote  ·  Ответ ~24ч  ·  Full-stack  ·  Prod  ·  @rcnn43  ·  ";

interface Props { text?: string }

export default function Ticker({ text = DEFAULT_LOOP }: Props) {
  return (
    <div className="w-full overflow-hidden border-t border-edge">
      <div className="animate-ticker py-3" style={{ display: 'flex', width: 'max-content' }}>
        <span className="font-mono text-[11px] text-muted tracking-[0.15em] whitespace-nowrap">
          {text}
        </span>
        <span
          className="font-mono text-[11px] text-muted tracking-[0.15em] whitespace-nowrap"
          aria-hidden
        >
          {text}
        </span>
      </div>
    </div>
  );
}
