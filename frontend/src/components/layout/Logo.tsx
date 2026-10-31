export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex size-8 items-center justify-center rounded-lg bg-brand-400">
        <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="#0d2927" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
          <path d="M12 4a8 8 0 1 0 8 8" />
          <circle cx="20" cy="4" r="1.5" fill="#0d2927" stroke="none" />
        </svg>
      </div>
      <span className="text-lg font-semibold tracking-tight text-white">Brightloop</span>
    </div>
  )
}
