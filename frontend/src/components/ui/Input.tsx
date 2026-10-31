import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'

interface FieldProps {
  label: string
  error?: string
  hint?: string
}

const base =
  'block w-full rounded-md border bg-white px-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-700 focus:outline-2 focus:outline-offset-0 focus:outline-brand-400/60 disabled:bg-gray-100'

export function Input({ label, error, hint, className = '', ...rest }: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId()
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-gray-800">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        className={`${base} h-10 ${error ? 'border-red-500' : 'border-gray-300'}`}
        {...rest}
      />
      {hint && !error && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

export function Textarea({ label, error, hint, className = '', ...rest }: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = useId()
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-gray-800">
        {label}
      </label>
      <textarea
        id={id}
        rows={3}
        aria-invalid={error ? true : undefined}
        className={`${base} py-2 ${error ? 'border-red-500' : 'border-gray-300'}`}
        {...rest}
      />
      {hint && !error && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
