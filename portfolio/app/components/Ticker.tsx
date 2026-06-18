const LOOP =
  "Принимаю проекты  ·  Remote  ·  Ответ ~24ч  ·  Full-stack  ·  Prod  ·  @rcnn43        ";

export default function Ticker() {
  return (
    <div className="w-full overflow-hidden border-t border-edge">
      <div className="flex animate-ticker py-3">
        <span className="font-mono text-[11px] text-muted tracking-[0.15em] whitespace-nowrap">
          {LOOP}
        </span>
        <span
          className="font-mono text-[11px] text-muted tracking-[0.15em] whitespace-nowrap"
          aria-hidden
        >
          {LOOP}
        </span>
        <span
          className="font-mono text-[11px] text-muted tracking-[0.15em] whitespace-nowrap"
          aria-hidden
        >
          {LOOP}
        </span>
      </div>
    </div>
  );
}
