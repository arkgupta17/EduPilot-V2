'use client'
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { useEffect, useRef, useState } from 'react'
import {
  ArrowUp,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  FileText,
  Globe2,
  Menu,
  MessageSquare,
  PanelRight,
  Plus,
  Search,
  Sparkles,
  Sun,
  Moon,
  X,
  Paperclip,
  Trash2,
} from 'lucide-react'

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

type Source = {
  heading: string
  url: string
  score: number
}

type KnowledgeDocument = {
  document_id: string
  source_id: string | null
  title: string
  url: string
  source_type: string
  chunks: number
}

type Message = {
  role: 'user' | 'assistant'
  text: string
  sources?: Source[]
}

const suggestions = [
  ['Programme essentials', 'What are the most important things I should know about this programme?', BookOpen],
  ['Admission requirements', 'What are the admission requirements for this programme?', Check],
  ['Analyse my resume', 'How does my profile align with this programme?', FileText],
  ['Explore my projects', 'What projects are mentioned in my resume?', Sparkles],
] as const


function Brand() {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#20291f] text-[#e8ebdd] shadow-sm">
        <svg
          viewBox="0 0 40 40"
          className="h-8 w-8"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M10 30V10H22C28 10 31 13 31 18C31 23 28 26 22 26H16"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M10 20H22"
            stroke="#A7B99A"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <circle cx="30" cy="30" r="2.5" fill="#A7B99A" />
        </svg>
      </div>

      <div className="min-w-0">
        <div className="text-[17px] font-semibold leading-tight tracking-[-0.045em] text-[#20231f]">
          EduPilot<span className="text-[#71816a]">.</span>
        </div>
      </div>
    </div>
  )
}


function Sidebar({
  collapsed,
  onToggle,
  onNewChat,
  messages,
  knowledgeDocuments,
  loadingDocuments,
  activeDocumentId,
  onSelectDocument,
  onDeleteDocument,
  
}: {
  collapsed: boolean
  onToggle: () => void
  onNewChat: () => void
  messages: Message[]
  knowledgeDocuments: KnowledgeDocument[]
  loadingDocuments: boolean
  activeDocumentId: string | null
  onSelectDocument: (document: KnowledgeDocument) => void
  onDeleteDocument: (document: KnowledgeDocument) => void
}) {
  const firstQuestion = messages.find((m) => m.role === 'user')?.text

  return (
    <aside
      className={`flex h-screen shrink-0 flex-col border-r border-slate-200/80 bg-[#fafaf9] transition-all duration-200 ${
        collapsed ? 'w-[72px]' : 'w-[272px]'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-5">
        {!collapsed && <Brand />}

        <button
          type="button"
          onClick={onToggle}
          className="ml-auto hidden h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-slate-300 hover:text-slate-900 md:flex"
          aria-label="Collapse sidebar"
        >
          <ChevronRight
            size={16}
            className={collapsed ? '' : 'rotate-180'}
          />
        </button>
      </div>

      <div className="px-3">
        <button
          type="button"
          onClick={onNewChat}
          className={`flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 text-sm font-medium text-white transition hover:bg-slate-800 ${
            collapsed ? 'px-0' : 'px-3'
          }`}
        >
          <Plus size={16} />
          {!collapsed && <span>New conversation</span>}
        </button>
      </div>

      {!collapsed && (
        <>
          <div className="px-3 pt-5">
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-400">
              <Search size={15} />
              <span className="text-xs">Conversation search</span>
            </div>
          </div>

          <div className="px-3 pt-6">
            <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Knowledge sources
            </div>

            <div className="max-h-[42vh] space-y-1.5 overflow-y-auto pr-1">
              {loadingDocuments ? (
                <div className="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-xs text-slate-400">
                  Loading sources...
                </div>
              ) : knowledgeDocuments.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-xs leading-5 text-slate-400">
                  No knowledge sources indexed yet.
                </div>
              ) : (
                knowledgeDocuments.map((document) => {
                  const isActive =
                    activeDocumentId === document.document_id

                  const isPdf =
                    document.source_type === 'pdf' ||
                    document.url.toLowerCase().endsWith('.pdf')

                  return (
                    <div
                      key={document.document_id}
                      onClick={() => onSelectDocument(document)}
                      className={`group flex w-full cursor-pointer items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left transition-colors duration-150 ${
  isActive
    ? 'border-[#e0e7db] bg-[#f1f4ee] text-slate-900'
    : 'border-transparent bg-transparent text-slate-800'
}`}
                    >
                      {/* Document icon */}
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                          isActive
  ? 'bg-slate-300 text-slate-700'
  : 'bg-slate-50 text-slate-500'
                        }`}
                      >
                        {isPdf ? (
                          <FileText size={15} />
                        ) : (
                          <Globe2 size={15} />
                        )}
                      </div>

                      {/* Document information */}
                      <div className="min-w-0 flex-1">
                        <div
                          className={`truncate text-xs font-semibold ${
                            isActive
  ? 'text-[#293629]'
  : 'text-slate-800'
                          }`}
                        >
                          {document.title}
                        </div>

                        <div
                          className={`mt-0.5 text-[10px] ${
                            isActive
  ? 'text-[#667760]'
  : 'text-slate-400'
                          }`}
                        >
                          {isPdf ? 'PDF' : 'Website'} · {document.chunks} chunks
                        </div>
                      </div>

                      {/* Delete button */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()

                          if (
                            window.confirm(
                              `Delete "${document.title}" from the knowledge base?`
                            )
                          ) {
                            console.log("DELETE CLICKED:", document)
                            onDeleteDocument(document)
                          }
                        }}
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition ${
                          isActive
                            ? 'text-slate-300 hover:bg-white/10 hover:text-red-300'
                            : 'text-slate-400 hover:bg-red-50 hover:text-red-600'
                        }`}
                        aria-label={`Delete ${document.title}`}
                        title="Delete source"
                      >
                        <Trash2 size={14} />
                      </button>

                      {/* Active indicator */}
                      {isActive && (
                        <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>

          <div className="px-4 pt-6">
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Current conversation
            </div>

            {firstQuestion ? (
              <div className="flex items-start gap-2.5 rounded-xl bg-white px-3 py-3 ring-1 ring-slate-200/70">
                <MessageSquare
                  size={15}
                  className="mt-0.5 shrink-0 text-slate-500"
                />

                <span className="line-clamp-2 text-xs leading-5 text-slate-600">
                  {firstQuestion}
                </span>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-xs leading-5 text-slate-400">
                Start a conversation to build context.
              </div>
            )}
          </div>
        </>
      )}

      <div className="mt-auto border-t border-slate-200/80 p-3">
        <div
          className={`flex items-center gap-3 rounded-xl px-2 py-2 ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[11px] font-semibold text-white">
            AI
          </div>

          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-slate-800">
                Ark
              </p>

              <p className="truncate text-[11px] text-slate-400">
                Personal workspace
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}

function Header({
  onMenu,
  onSources,
  sourceCount,
  darkMode,
  onToggleTheme,
}: {
  onMenu: () => void
  onSources: () => void
  sourceCount: number
  darkMode: boolean
  onToggleTheme: () => void
}) {
  return (
    <header className="flex h-[68px] shrink-0 items-center border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-xl md:px-7">
      <button type="button" className="mr-3 flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 md:hidden" onClick={onMenu} aria-label="Open navigation">
        <Menu size={18} />
      </button>

      <div className="hidden md:block">
        <p className="text-sm font-semibold text-slate-900">Programme intelligence</p>
        <p className="text-[11px] text-slate-400">Ask questions across your indexed knowledge</p>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-medium text-emerald-700 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          AI ready
        </div>

        <button type="button" onClick={onSources} className="flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-950">
          <PanelRight size={15} />
          <span className="hidden sm:inline">Evidence{sourceCount ? ` · ${sourceCount}` : ''}</span>
        </button>

        <button
          type="button"
          onClick={onToggleTheme}
          className="flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 text-slate-600 transition hover:border-slate-300 hover:text-slate-950"
          aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {darkMode ? <Sun size={15} /> : <Moon size={15} />}
          <span className="hidden lg:inline text-[11px] font-medium">
            {darkMode ? 'Light' : 'Dark'}
          </span>
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-[11px] font-semibold text-white">AK</div>
      </div>
    </header>
  )
}

function SourceCard({ source }: { source: Source }) {
  const [open, setOpen] = useState(false)
  const isPdf = source.url.toLowerCase().includes('.pdf')
  const Icon = isPdf ? FileText : Globe2
  const fileName = isPdf ? source.url.split('\\').pop() || source.heading : source.heading

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
      <button type="button" className="flex w-full items-center gap-3 text-left" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-slate-500">
          <Icon size={15} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-slate-800">{fileName}</p>
          <p className="mt-0.5 truncate text-[11px] text-slate-400">{source.heading}</p>
        </div>
        <ChevronDown size={14} className={`shrink-0 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="mt-3 border-t border-slate-100 pt-3">
          <p className="text-[11px] leading-5 text-slate-500">Retrieved from the EduPilot knowledge base for this answer.</p>
          <p className="mt-2 break-all text-[10px] leading-4 text-slate-400">{source.url}</p>
        </div>
      )}
    </div>
  )
}

function InlineSources({ sources, onViewAll }: { sources: Source[]; onViewAll: () => void }) {
  if (!sources.length) return null
  const visible = sources.slice(0, 2)
  const remaining = Math.max(sources.length - visible.length, 0)

  return (
    <button type="button" onClick={onViewAll} className="mt-4 flex max-w-full items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left shadow-[0_1px_2px_rgba(15,23,42,0.03)] transition hover:border-slate-300">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-white"><Sparkles size={13} /></div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-semibold text-slate-700">Grounded in {sources.length} {sources.length === 1 ? 'source' : 'sources'}</div>
        <div className="mt-1 flex min-w-0 items-center gap-1.5">
          {visible.map((source, index) => (
            <span key={`${source.url}-${source.heading}-${index}`} className="max-w-[150px] truncate rounded-md bg-slate-50 px-1.5 py-1 text-[10px] text-slate-500">
              {source.url.toLowerCase().includes('.pdf') ? 'PDF' : 'WEB'} · {source.heading}
            </span>
          ))}
          {remaining > 0 && <span className="shrink-0 text-[10px] font-medium text-slate-400">+{remaining}</span>}
        </div>
      </div>
      <ChevronRight size={14} className="shrink-0 text-slate-400" />
    </button>
  )
}

function Composer({
  onSend,
  onUpload,
  onIngestUrl,
  disabled,
  uploading,
  ingestingUrl
}: {
  onSend: (value: string) => void
  onUpload: (file: File) => void
  onIngestUrl: (url: string) => void
  ingestingUrl?: boolean
  disabled: boolean
  uploading: boolean
}) {
  const [value, setValue] = useState('')
  const [url, setUrl] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const submit = () => {
    const trimmed = value.trim()

    if (!trimmed || disabled || uploading) {
      return
    }

    onSend(trimmed)
    setValue('')
  }

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0]

    if (file) {
      onUpload(file)
    }

    event.target.value = ''
  }

  const handleUrlSubmit = () => {
   const cleanUrl = url.trim()

  if (!cleanUrl) return

  onIngestUrl(cleanUrl)
  setUrl('')
}

  return (
    <div className="rounded-2xl border border-slate-300 bg-white p-2 shadow-[0_12px_40px_rgba(15,23,42,0.08)] ring-1 ring-black/[0.02]">

      {/* Message input */}
      <textarea
        value={value}
        disabled={disabled || uploading}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (
            e.key === 'Enter' &&
            !e.shiftKey &&
            !e.nativeEvent.isComposing &&
            e.keyCode !== 229
          ) {
            e.preventDefault()
            submit()
          }
        }}
        placeholder="Ask EduPilot anything about the programme or your documents..."
        rows={1}
        className="max-h-32 min-h-[44px] w-full resize-none border-0 bg-transparent px-3 py-2.5 text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400"
      />

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Bottom controls */}
      <div className="flex items-center justify-between gap-2 px-1 pb-0.5">

           {/* URL INPUT */}
         <div className="flex items-center gap-2">
           <input
            type="url"
            value={url}
            disabled={disabled || uploading || ingestingUrl}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleUrlSubmit()
              }
            }}
            placeholder="Paste a website URL..."
            className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 outline-none placeholder:text-slate-400 focus:border-slate-400"
          />
        

    <button
      type="button"
      onClick={handleUrlSubmit}
      disabled={
        !url.trim() ||
        disabled ||
        uploading ||
        ingestingUrl
      }
      className="flex h-9 shrink-0 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {ingestingUrl ? 'Adding…' : 'Add URL'}
    </button>
  </div>

  {/* EXISTING CONTROLS */}
  <div className="flex items-center justify-between gap-2">

    <div className="flex min-w-0 items-center gap-2"></div>

          {/* UPLOAD BUTTON */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || uploading}
            className="flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Upload document"
            title="Upload PDF document"
          >
            <Paperclip size={15} />

            <span className="hidden sm:inline">
              {uploading ? 'Uploading…' : 'Upload'}
            </span>
          </button>

          <span className="hidden truncate px-1 text-[10px] text-slate-400 sm:inline">
            PDF documents
          </span>

        </div>

        {/* SEND BUTTON */}
        <button
          type="button"
          onClick={submit}
          disabled={
            !value.trim() ||
            disabled ||
            uploading
          }
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
          aria-label="Send message"
        >
          <ArrowUp size={17} />
        </button>

      </div>
    </div>
  )
}

function Welcome({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  return (
    <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col justify-center px-5 py-14 sm:px-8">
      <div className="mb-7 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-950/10">
        <Sparkles size={21} />
      </div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Your programme intelligence layer</p>
      <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-5xl">
        Research the programme.
        <br />
        Understand where you fit.
      </h1>
      <p className="mt-5 max-w-2xl text-sm leading-6 text-slate-500 sm:text-[15px]">
        Ask natural questions about the programme, admissions, curriculum, or your own profile. EduPilot answers from indexed evidence instead of making you search through documents manually.
      </p>

      <div className="mt-9 grid gap-2 sm:grid-cols-2">
{suggestions.map(([label, prompt, Icon]) => (
  <button
    key={label}
    type="button"
    onClick={() => onSuggestion(prompt)}
    className="group flex min-h-[72px] items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-[0_12px_30px_rgba(15,23,42,0.07)]"
  >
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-600 transition group-hover:bg-slate-950 group-hover:text-white">
      <Icon size={16} />
    </span>

    <span className="min-w-0 flex-1">
      <span className="block text-xs font-semibold text-slate-800">
        {label}
      </span>
      <span className="mt-1 block line-clamp-1 text-[11px] text-slate-400">
        {prompt}
      </span>
    </span>

    <ChevronRight
      size={15}
      className="text-slate-300 transition group-hover:text-slate-600"
    />
  </button>
))}
      </div>
    </div>
  )
}

function MessageList({ messages, loading, onSources }: { messages: Message[]; loading: boolean; onSources: (sources: Source[]) => void }) {
  return (
    <div className="mx-auto w-full max-w-4xl px-5 py-8 sm:px-8">
      <div className="space-y-8">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.role === 'assistant' && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm"><Sparkles size={14} /></div>
            )}

            <div className={message.role === 'user'
              ? 'max-w-[82%] rounded-2xl rounded-br-md bg-slate-950 px-4 py-3 text-[14px] font-medium leading-[1.8] tracking-[0.005em] text-white shadow-sm [font-family:var(--font-geist-sans)]'
              : 'max-w-[88%] min-w-0 pt-0.5 text-[15px] leading-[1.85] tracking-[0.005em] text-[#353b34] [font-family:var(--font-geist-sans)]'}>
              {message.role === 'assistant' && (
                <div className="mb-1.5 flSex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-900">EduPilot</span>
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-emerald-700">Grounded</span>
                </div>
              )}
              <div className="text-[14px] leading-7 text-slate-700">
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      h1: ({ children }) => (
        <h1 className="mb-3 mt-5 text-lg font-bold text-slate-900 first:mt-0">
          {children}
        </h1>
      ),
      h2: ({ children }) => (
        <h2 className="mb-2 mt-5 text-base font-bold text-slate-900 first:mt-0">
          {children}
        </h2>
      ),
      h3: ({ children }) => (
        <h3 className="mb-2 mt-4 text-sm font-bold text-slate-900">
          {children}
        </h3>
      ),
      p: ({ children }) => (
        <p className="mb-3 last:mb-0">
          {children}
        </p>
      ),
      strong: ({ children }) => (
        <strong className="font-semibold text-slate-900">
          {children}
        </strong>
      ),
      ul: ({ children }) => (
        <ul className="mb-3 ml-5 list-disc space-y-1">
          {children}
        </ul>
      ),
      ol: ({ children }) => (
        <ol className="mb-3 ml-5 list-decimal space-y-1">
          {children}
        </ol>
      ),
      li: ({ children }) => (
        <li className="pl-1">
          {children}
        </li>
      ),
      table: ({ children }) => (
        <div className="my-4 overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full border-collapse text-sm">
            {children}
          </table>
        </div>
      ),
      thead: ({ children }) => (
        <thead className="bg-slate-100">
          {children}
        </thead>
      ),
      th: ({ children }) => (
        <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-900">
          {children}
        </th>
      ),
      td: ({ children }) => (
        <td className="border-b border-slate-200 px-3 py-2">
          {children}
        </td>
      ),
      blockquote: ({ children }) => (
        <blockquote className="my-3 border-l-4 border-slate-300 pl-4 text-slate-600">
          {children}
        </blockquote>
      ),
      code: ({ children }) => (
        <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[13px]">
          {children}
        </code>
      ),
    }}
  >
    {message.text}
  </ReactMarkdown>
</div>
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <InlineSources sources={message.sources} onViewAll={() => onSources(message.sources || [])} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white"><Sparkles size={14} /></div>
            <div className="flex items-center gap-2 pt-1 text-xs text-slate-400">
              <span className="flex gap-1">
                <i className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" />
                <i className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
                <i className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
              </span>
              Searching the knowledge base…
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function EvidencePanel({ sources, onClose }: { sources: Source[]; onClose: () => void }) {
  return (
    <aside className="hidden w-[340px] shrink-0 border-l border-slate-200/80 bg-[#fafaf9] xl:block">
      <div className="sticky top-0 flex h-[68px] items-center justify-between border-b border-slate-200/80 bg-[#fafaf9]/95 px-5 backdrop-blur-xl">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Evidence</p>
          <h2 className="mt-0.5 text-sm font-semibold text-slate-900">Sources</h2>
        </div>
        <button type="button" onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-white hover:text-slate-800" aria-label="Close sources">
          <X size={15} />
        </button>
      </div>

      <div className="h-[calc(100vh-68px)] overflow-y-auto p-4">
        {sources.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-8 text-center">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm ring-1 ring-slate-200"><PanelRight size={18} /></div>
            <p className="mt-4 text-xs font-medium text-slate-700">Evidence will appear here</p>
            <p className="mt-1 text-[11px] leading-5 text-slate-400">Ask a question and EduPilot will show the sources used to ground the answer.</p>
          </div>
        ) : (
          <>
            <div className="mb-4 rounded-xl border border-slate-200 bg-white px-3 py-2.5">
              <div className="text-xs font-semibold text-slate-700">{sources.length} {sources.length === 1 ? 'source' : 'sources'} retrieved</div>
              <div className="mt-1 text-[10px] leading-4 text-slate-400">Evidence returned by the backend for the current answer.</div>
            </div>
            <div className="space-y-2">
              {sources.map((source, index) => (
                <SourceCard key={`${source.url}-${source.heading}-${index}`} source={source} />
              ))}
            </div>
          </>
        )}
      </div>
    </aside>
  )
}

export default function EduPilotDashboard() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)
  const [showSources, setShowSources] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [ingestingUrl, setIngestingUrl] = useState(false)
  const [sources, setSources] = useState<Source[]>([])
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<KnowledgeDocument[]>([])
  const [loadingDocuments, setLoadingDocuments] = useState(false)
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null)
  const [activeSourceName, setActiveSourceName] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null)
  const [activeDocumentName, setActiveDocumentName] = useState<string | null>(null)
  
  


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  useEffect(() => {
    const savedTheme = window.localStorage.getItem('edupilot-theme')
    if (savedTheme === 'dark') setDarkMode(true)
  }, [])

  useEffect(() => {
    window.localStorage.setItem('edupilot-theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  useEffect(() => {
  const loadKnowledgeDocuments = async () => {
    setLoadingDocuments(true)

    try {
      const response = await fetch(
        `${API_URL}/api/documents`,
        {
          headers: {
            Accept: 'application/json',
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to load documents: ${response.status}`)
      }

      const data = await response.json()

      setKnowledgeDocuments(
        Array.isArray(data) ? data : []
      )
    } catch (error) {
      console.error(
        'Failed to load knowledge documents:',
        error
      )
    } finally {
      setLoadingDocuments(false)
    }
  }

  loadKnowledgeDocuments()
}, [])

  
const newChat = () => {
  if (loading) return

  setMessages([])
  setSources([])

  // Clear the previous conversation's knowledge scope
  setActiveDocumentId(null)
  setActiveDocumentName(null)
  setActiveSourceId(null)
  setActiveSourceName(null)

  setMobileMenu(false)
}


  const selectKnowledgeDocument = (
  document: KnowledgeDocument
) => {
  console.log('DOCUMENT CLICKED:', document)
  console.log('DOCUMENT ID:', document.document_id)
  console.log('SOURCE ID:', document.source_id)

  setActiveDocumentId(document.document_id)
  setActiveDocumentName(document.title)

  setActiveSourceId(document.source_id)
  setActiveSourceName(document.title)

  setMessages((prev) => [
    ...prev,
    {
      role: 'assistant',
      text: `Knowledge source switched to **${document.title}**. You can now ask questions about this source.`,
      sources: [],
    },
  ])
}

const deleteKnowledgeDocument = async (document: KnowledgeDocument) => {
  try {
    console.log('Deleting document:', document.document_id)

    const response = await fetch(
      `${API_URL}/api/documents?document_id=${encodeURIComponent(
        document.document_id
      )}`,
      {
        method: 'DELETE',
      }
    )

    const data = await response.json()

    console.log('DELETE response status:', response.status)
    console.log('DELETE response data:', data)

    if (!response.ok) {
      throw new Error(
        data?.detail || 'Failed to delete document.'
      )
    }

    setKnowledgeDocuments((prev) =>
      prev.filter(
        (item) => item.document_id !== document.document_id
      )
    )

    if (activeDocumentId === document.document_id) {
      setActiveDocumentId(null)
      setActiveDocumentName(null)
      setActiveSourceId(null)
      setActiveSourceName(null)
      setSources([])
    }

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text: `"${document.title}" was deleted from the knowledge base.`,
        sources: [],
      },
    ])
  } catch (error) {
    console.error('Delete document error:', error)
  }
}

  const ingestUrl = async (url: string) => {
  setIngestingUrl(true)

  try {
    const response = await fetch(
      `${API_URL}/api/documents/ingest-url`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          url,
        }),
      }
    )

    const data = await response.json()

    console.log("INGEST RESPONSE:", data)

    if (!response.ok) {
      throw new Error(
        data?.detail || 'Website ingestion failed.'
      )
    }

    if (!data.source_id) {
      throw new Error(
        'Website was indexed, but no source_id was returned.'
      )
    }

    // Activate this website as the current knowledge source
    setActiveSourceId(data.source_id)
    setActiveSourceName(url)

    // Clear PDF scope
    setActiveDocumentId(data.document_id)
    setActiveDocumentName(url)

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text: `Website added successfully. ${data.pages_crawled} page(s) and ${data.chunks} chunk(s) indexed. You can now ask questions about this website.`,
      },
    ])
  } catch (error) {
    console.error('Website ingestion error:', error)

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text:
          error instanceof Error
            ? error.message
            : 'Website ingestion failed.',
      },
    ])
  } finally {
    setIngestingUrl(false)
  }
}
  const uploadDocument = async (file: File) => {
  if (uploading) {
    return
  }

  // ---------------------------------------------
  // Validate file
  // ---------------------------------------------

  const isPdf =
    file.type === 'application/pdf' ||
    file.name.toLowerCase().endsWith('.pdf')

  if (!isPdf) {
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text: 'Please upload a PDF document.',
        sources: [],
      },
    ])

    return
  }

  // ---------------------------------------------
  // Start upload
  // ---------------------------------------------

  setUploading(true)

  try {
    const formData = new FormData()

    formData.append(
      'file',
      file
    )

    const response = await fetch(
      `${API_URL}/api/documents/upload`,
      {
        method: 'POST',
        body: formData,
      }
    )

    // -------------------------------------------
    // Backend error
    // -------------------------------------------

    if (!response.ok) {
      const detail = await response.text()

      throw new Error(
        detail ||
        `Upload failed: ${response.status}`
      )
    }

    // -------------------------------------------
    // Parse response
    // -------------------------------------------

 const data = await response
  .json()
  .catch(() => ({}))

 if (!data.document_id) {
  throw new Error(
    "Upload succeeded but no document ID was returned."
  )
}

 setActiveDocumentId(data.document_id)
 setActiveDocumentName(
  data.filename || file.name
 )

 const message =
  data.message ||
  data.detail ||
  `${file.name} uploaded successfully.`

    // -------------------------------------------
    // Show success in conversation
    // -------------------------------------------

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text:
          `${message}\n\n` +
          `You can now ask questions about the uploaded document.`,
        sources: [],
      },
    ])

  } catch (error) {

    console.error(
      'EduPilot upload error:',
      error
    )

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        text:
          'I could not upload that document. ' +
          'Make sure the FastAPI server is running ' +
          'and that POST /api/documents/upload is available.',
        sources: [],
      },
    ])

  } finally {

    setUploading(false)

  }
}

  const send = async (text: string) => {
    
if (!text.trim() || loading) return

const cleanText = text.trim()

// Never query the knowledge base without an explicit source
if (!activeDocumentId && !activeSourceId) {
  setMessages((prev) => [
    ...prev,
    { role: 'user', text: cleanText },
    {
      role: 'assistant',
      text:
        'Please select a knowledge Source, ' +
        'Upload a PDF document, or ingest a website URL before asking a question.',
      sources: [],
    },
  ])
  setSources([])
  return
}

    const userMessage: Message = { role: 'user', text: cleanText }

    const history = messages.map((message) => ({
      role: message.role,
      content: message.text,
    }))

    setMessages((prev) => [...prev, userMessage])
    setSources([])
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
        query: cleanText,
        history,
        document_id: activeDocumentId,
        source_id: activeSourceId,
        }),     
      })

      if (!response.ok) throw new Error(`API request failed: ${response.status}`)

      const data = await response.json()
      const answer = data.answer || "I don't know based on the available information."
      const retrievedSources: Source[] = Array.isArray(data.sources) ? data.sources : []

      setSources(retrievedSources)
      setMessages((prev) => [...prev, { role: 'assistant', text: answer, sources: retrievedSources }])
    } catch (error) {
      console.error('EduPilot API error:', error)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        text: 'I could not connect to EduPilot. Please make sure the FastAPI server is running and the API URL is correct.',
        sources: [],
      }])
      setSources([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`edupilot-shell flex h-screen overflow-hidden bg-white text-slate-950 ${darkMode ? 'edupilot-dark' : ''}`}>
            <style jsx global>{`

        .edupilot-dark {
          background: #111311 !important;
          color: #e8eae5 !important;
          color-scheme: dark;
        }

        /* Main canvas */
        .edupilot-dark main {
          background-color: #111311 !important;
        }

        /* Sidebar and top-level surfaces */
        .edupilot-dark .bg-white,
        .edupilot-dark .bg-white\\/90,
        .edupilot-dark .bg-white\\/95,
        .edupilot-dark .bg-\\[\\#fafaf9\\] {
          background-color: #171a17 !important;
        }

        /* Header and footer surfaces */
        .edupilot-dark header {
          background-color: #171a17 !important;
        }

        /* Text hierarchy */
        .edupilot-dark .text-slate-950,
        .edupilot-dark .text-slate-900,
        .edupilot-dark .text-slate-800,
        .edupilot-dark .text-slate-700 {
          color: #e7e9e3 !important;
        }

        .edupilot-dark .text-slate-600 {
          color: #b7bcb2 !important;
        }

        .edupilot-dark .text-slate-500 {
          color: #9ba195 !important;
        }

        .edupilot-dark .text-slate-400,
        .edupilot-dark .text-slate-300 {
          color: #858b7f !important;
        }

        /* Consistent, understated borders */
        .edupilot-dark .border-slate-200,
        .edupilot-dark .border-slate-200\\/80,
        .edupilot-dark .border-slate-100,
        .edupilot-dark .border-slate-300,
        .edupilot-dark .border-t,
        .edupilot-dark .border-r,
        .edupilot-dark .border-l {
          border-color: #30352e !important;
        }

        /* Secondary surfaces and cards */
        .edupilot-dark .bg-slate-50,
        .edupilot-dark .bg-slate-100 {
          background-color: #1d211c !important;
        }

        .edupilot-dark .bg-slate-200 {
          background-color: #292e27 !important;
        }

        /* New Conversation — readable, understated */
        .edupilot-dark aside button.bg-slate-950 {
          background-color: #292e27 !important;
          color: #e8ebe4 !important;
          border: 1px solid #3a4035 !important;
          box-shadow: none !important;
        }

        .edupilot-dark aside button.bg-slate-950:hover {
          background-color: #292e27 !important;
          color: #e8ebe4 !important;
        }

        /* Knowledge source selection */
        .edupilot-dark aside .group {
          color: #dfe3da !important;
          box-shadow: none !important;
        }

        .edupilot-dark aside .group .text-slate-800 {
          color: #e1e5dc !important;
        }

        /* Composer and URL input */
        .edupilot-dark textarea,
        .edupilot-dark input {
          background-color: #191c18 !important;
          color: #e8ebe4 !important;
          border-color: #343a31 !important;
          box-shadow: none !important;
        }

        .edupilot-dark textarea::placeholder,
        .edupilot-dark input::placeholder {
          color: #858c80 !important;
          opacity: 1;
        }

        .edupilot-dark textarea:focus,
        .edupilot-dark input:focus {
          border-color: #626b58 !important;
          outline: none;
          box-shadow: 0 0 0 1px #626b58 !important;
        }

        /* Upload and secondary buttons */
        .edupilot-dark button.border-slate-200,
        .edupilot-dark button.border-slate-300 {
          border-color: #363c33 !important;
        }

        /* Composer shadow */
        .edupilot-dark .shadow-\\[0_12px_40px_rgba\\(15\\,23\\,42\\,0\\.08\\)\\] {
          box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12) !important;
        }

        /* Avoid bright default card shadows */
        .edupilot-dark .shadow-sm,
        .edupilot-dark .shadow-md {
          box-shadow: none !important;
        }

        /* Evidence panel: override light header surfaces */
        .edupilot-dark aside header,
        .edupilot-dark [class*="context-header"] {
          background-color: #171a17 !important;
          color: #e7e9e3 !important;
          border-color: #30352e !important;
        }

        /* Preserve readability of disabled controls */
        .edupilot-dark button:disabled {
          opacity: 0.55;
        }
      `}</style>
      <div className="hidden md:block">
        <Sidebar
  collapsed={collapsed}
  onToggle={() => setCollapsed((v) => !v)}
  onNewChat={newChat}
  messages={messages}
  knowledgeDocuments={knowledgeDocuments}
  loadingDocuments={loadingDocuments}
  activeDocumentId={activeDocumentId}
  onSelectDocument={selectKnowledgeDocument}
  onDeleteDocument={deleteKnowledgeDocument}
/>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
            onMenu={() => setMobileMenu(true)}
            onSources={() => setShowSources((v) => !v)}
            sourceCount={sources.length}
            darkMode={darkMode}
            onToggleTheme={() => setDarkMode((value) => !value)}
          />

        {mobileMenu && (
          <div className="fixed inset-0 z-50 bg-slate-950/20 backdrop-blur-sm md:hidden" onClick={() => setMobileMenu(false)}>
            <div className="h-full w-[290px] bg-[#fafaf9] p-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between pb-5">
                <Brand />
                <button type="button" onClick={() => setMobileMenu(false)} className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500" aria-label="Close navigation">
                  <X size={17} />
                </button>
              </div>
              <button type="button" onClick={newChat} className="flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 text-sm font-medium text-white">
                <Plus size={16} /> New conversation
              </button>
              <div className="mt-6 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Current conversation</div>
              <div className="mt-2 rounded-xl bg-white px-3 py-3 text-xs leading-5 text-slate-600 ring-1 ring-slate-200/70">
                {messages.find((m) => m.role === 'user')?.text || 'No conversation yet.'}
              </div>
            </div>
          </div>
        )}

        <div className="flex min-h-0 flex-1">
          <main className="relative flex min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto">
              {messages.length === 0 ? (
                <Welcome
  onSuggestion={(prompt) => {
    console.log('Selected document:', activeDocumentId)
    console.log('Selected source:', activeSourceId)
    console.log('Shortcut prompt:', prompt)

    if (!activeDocumentId && !activeSourceId) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: 'Please select an existing knowledge source from the sidebar, upload a PDF, or ingest a website URL before using these shortcuts.',
          sources: [],
        },
      ])
      return
    }

    void send(prompt)
  }}
/>
              ) : (
                <MessageList
                  messages={messages}
                  loading={loading}
                  onSources={(value) => {
                    setSources(value)
                    setShowSources(true)
                  }}
                />
              )}
              <div ref={bottomRef} />
            </div>

            <div className="border-t border-slate-100 bg-white/95 px-4 pb-4 pt-3 backdrop-blur-xl sm:px-6">
              <div className="mx-auto w-full max-w-4xl">
                <Composer onSend={send} disabled={loading} onUpload={uploadDocument} uploading={uploading} onIngestUrl={ingestUrl} ingestingUrl={ingestingUrl} />
                <p className="mt-2 text-center text-[10px] text-slate-400">EduPilot answers from your indexed knowledge base.</p>
              </div>
            </div>
          </main>

          {showSources && (
            <EvidencePanel sources={sources} onClose={() => setShowSources(false)} />
          )}
        </div>
      </div>
    </div>
  )
}