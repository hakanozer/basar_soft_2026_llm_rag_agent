import axios from 'axios'
import { useEffect, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import './App.css'

type ConversationMode = 'chat' | 'agent'
type MessageRole = 'user' | 'assistant'

type IntentFilters = Record<string, string | number | string[] | null>

interface IntentPayload {
  intent?: string
  confidence?: number
  filters?: IntentFilters
  original_query?: string
  language?: string
}

interface ProductPayload {
  id: number
  name: string
  category: string
  price: number
  original_price?: number
  brand?: string
  color?: string
  season?: string
  gender?: string
  stock_quantity?: number
  rating?: number
  description?: string
  features?: string
  sizes?: string
  review_count?: number
  discount_rate?: number
}

interface ChatResponse {
  answer: string
  intent?: IntentPayload
  products?: ProductPayload[]
  total_found?: number
  answer_time_ms?: number
}

interface AgentResponse {
  prompt: string
  user_id: string
}

interface AgentHistoryItem {
  role: 'user' | 'assistant'
  content: string
}

interface AgentHistoryResponse {
  user_id: string
  history: AgentHistoryItem[]
}

interface MessageMeta {
  intent?: IntentPayload
  products?: ProductPayload[]
  totalFound?: number
  answerTimeMs?: number
}

interface MessageItem {
  id: string
  role: MessageRole
  content: string
  createdAt: string
  meta?: MessageMeta
}

interface ConversationItem {
  id: string
  mode: ConversationMode
  title: string
  createdAt: string
  updatedAt: string
  userId?: string
  messages: MessageItem[]
}

interface ToastItem {
  id: string
  title: string
  description: string
}

interface StoredState {
  conversations: ConversationItem[]
  activeConversationId: string
}

const STORAGE_KEY = 'basar-soft-ai-app'
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
})

function createId() {
  return crypto.randomUUID()
}

function getNow() {
  return new Date().toISOString()
}

function buildMessage(
  role: MessageRole,
  content: string,
  meta?: MessageMeta,
): MessageItem {
  return {
    id: createId(),
    role,
    content,
    createdAt: getNow(),
    meta,
  }
}

function buildConversation(mode: ConversationMode): ConversationItem {
  const timestamp = getNow()

  return {
    id: createId(),
    mode,
    title: mode === 'chat' ? 'Yeni sohbet' : 'Yeni agent oturumu',
    createdAt: timestamp,
    updatedAt: timestamp,
    userId: mode === 'agent' ? createId() : undefined,
    messages: [],
  }
}

function sortConversations(conversations: ConversationItem[]) {
  return [...conversations].sort((left, right) =>
    right.updatedAt.localeCompare(left.updatedAt),
  )
}

function parseStoredState(): StoredState {
  const fallbackConversation = buildConversation('chat')

  try {
    const rawState = localStorage.getItem(STORAGE_KEY)
    if (!rawState) {
      return {
        conversations: [fallbackConversation],
        activeConversationId: fallbackConversation.id,
      }
    }

    const parsed = JSON.parse(rawState) as Partial<StoredState>
    const conversations = Array.isArray(parsed.conversations)
      ? sortConversations(parsed.conversations as ConversationItem[])
      : [fallbackConversation]
    const activeConversationId = conversations.some(
      (conversation) => conversation.id === parsed.activeConversationId,
    )
      ? (parsed.activeConversationId as string)
      : conversations[0].id

    return {
      conversations,
      activeConversationId,
    }
  } catch {
    return {
      conversations: [fallbackConversation],
      activeConversationId: fallbackConversation.id,
    }
  }
}

function updateConversation(
  conversations: ConversationItem[],
  conversationId: string,
  updater: (conversation: ConversationItem) => ConversationItem,
) {
  return sortConversations(
    conversations.map((conversation) =>
      conversation.id === conversationId ? updater(conversation) : conversation,
    ),
  )
}

function buildTitle(mode: ConversationMode, prompt: string) {
  const trimmed = prompt.trim().replace(/\s+/g, ' ')
  if (!trimmed) {
    return mode === 'chat' ? 'Yeni sohbet' : 'Yeni agent oturumu'
  }

  return trimmed.length > 42 ? `${trimmed.slice(0, 42)}...` : trimmed
}

function formatClock(timestamp: string) {
  return new Intl.DateTimeFormat('tr-TR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timestamp))
}

function parseArrayLike(value?: string) {
  if (!value) {
    return []
  }

  return value
    .replace(/\[|\]|'/g, '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function getConversationPreview(conversation: ConversationItem) {
  const lastMessage = conversation.messages[conversation.messages.length - 1]

  if (!lastMessage) {
    return conversation.mode === 'chat'
      ? 'Tek turlu soru-cevap akisi'
      : 'User id ile cok turlu agent akisi'
  }

  return lastMessage.content
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data

    if (typeof responseData?.detail === 'string') {
      return responseData.detail
    }

    if (typeof responseData?.message === 'string') {
      return responseData.message
    }

    if (typeof responseData?.error === 'string') {
      return responseData.error
    }

    if (error.response?.status) {
      return `Istek basarisiz oldu (${error.response.status})`
    }

    return 'Sunucuya ulasilamadi.'
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Beklenmeyen bir hata olustu.'
}

const initialState = parseStoredState()

function App() {
  const [conversations, setConversations] = useState<ConversationItem[]>(
    initialState.conversations,
  )
  const [activeConversationId, setActiveConversationId] = useState(
    initialState.activeConversationId,
  )
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isSyncingHistory, setIsSyncingHistory] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const activeConversation =
    conversations.find((conversation) => conversation.id === activeConversationId) ??
    conversations[0]

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        conversations,
        activeConversationId,
      }),
    )
  }, [activeConversationId, conversations])

  function pushToast(title: string, description: string) {
    const id = createId()

    setToasts((current) => [...current, { id, title, description }])

    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, 4200)
  }

  function handleCreateConversation(mode: ConversationMode) {
    const conversation = buildConversation(mode)
    setConversations((current) => [conversation, ...current])
    setActiveConversationId(conversation.id)
    setDraft('')
    setSidebarOpen(false)
  }

  function handleSelectConversation(conversationId: string) {
    setActiveConversationId(conversationId)
    setSidebarOpen(false)
  }

  async function handleDeleteConversation(conversationId: string) {
    const targetConversation = conversations.find(
      (conversation) => conversation.id === conversationId,
    )

    if (!targetConversation) {
      return
    }

    try {
      if (targetConversation.mode === 'agent' && targetConversation.userId) {
        await api.delete(`/api/v1/agent/${targetConversation.userId}`)
      }

      const remainingConversations = conversations.filter(
        (conversation) => conversation.id !== conversationId,
      )

      if (!remainingConversations.length) {
        const fallbackConversation = buildConversation('chat')
        setConversations([fallbackConversation])
        setActiveConversationId(fallbackConversation.id)
        setDraft('')
        return
      }

      setConversations(sortConversations(remainingConversations))

      if (activeConversationId === conversationId) {
        setActiveConversationId(sortConversations(remainingConversations)[0].id)
      }
    } catch (error) {
      pushToast('Sohbet silinemedi', getErrorMessage(error))
    }
  }

  function handleModeSwitch(mode: ConversationMode) {
    const existingConversation = conversations.find(
      (conversation) => conversation.mode === mode,
    )

    if (existingConversation) {
      setActiveConversationId(existingConversation.id)
      return
    }

    handleCreateConversation(mode)
  }

  async function handleSyncAgentHistory() {
    if (!activeConversation?.userId || activeConversation.mode !== 'agent') {
      return
    }

    setIsSyncingHistory(true)

    try {
      const response = await api.get<AgentHistoryResponse>(
        `/api/v1/agent/${activeConversation.userId}`,
      )

      const syncedMessages = response.data.history.map((item) =>
        buildMessage(item.role, item.content),
      )

      setConversations((current) =>
        updateConversation(current, activeConversation.id, (conversation) => ({
          ...conversation,
          updatedAt: getNow(),
          messages: syncedMessages,
          title:
            syncedMessages.length > 0
              ? buildTitle(conversation.mode, syncedMessages[0].content)
              : 'Yeni agent oturumu',
        })),
      )
    } catch (error) {
      pushToast('Gecmis yenilenemedi', getErrorMessage(error))
    } finally {
      setIsSyncingHistory(false)
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!activeConversation || isSending) {
      return
    }

    const prompt = draft.trim()
    if (!prompt) {
      return
    }

    const conversationId = activeConversation.id
    const userMessage = buildMessage('user', prompt)
    setDraft('')
    setIsSending(true)

    setConversations((current) =>
      updateConversation(current, conversationId, (conversation) => ({
        ...conversation,
        title:
          conversation.messages.length === 0
            ? buildTitle(conversation.mode, prompt)
            : conversation.title,
        updatedAt: getNow(),
        messages: [...conversation.messages, userMessage],
      })),
    )

    try {
      if (activeConversation.mode === 'chat') {
        const response = await api.get<ChatResponse>('/api/v1/chat', {
          params: { prompt },
        })

        const assistantMessage = buildMessage('assistant', response.data.answer, {
          intent: response.data.intent,
          products: response.data.products,
          totalFound: response.data.total_found,
          answerTimeMs: response.data.answer_time_ms,
        })

        setConversations((current) =>
          updateConversation(current, conversationId, (conversation) => ({
            ...conversation,
            updatedAt: getNow(),
            messages: [...conversation.messages, assistantMessage],
          })),
        )
      } else {
        const response = await api.post<AgentResponse>('/api/v1/agent', {
          user_id: activeConversation.userId,
          message: prompt,
        })

        const assistantMessage = buildMessage('assistant', response.data.prompt)

        setConversations((current) =>
          updateConversation(current, conversationId, (conversation) => ({
            ...conversation,
            userId: response.data.user_id || conversation.userId,
            updatedAt: getNow(),
            messages: [...conversation.messages, assistantMessage],
          })),
        )
      }
    } catch (error) {
      pushToast('Mesaj gonderilemedi', getErrorMessage(error))
    } finally {
      setIsSending(false)
    }
  }

  function handleInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()

      void sendMessage({
        preventDefault() {},
      } as FormEvent<HTMLFormElement>)
    }
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div>
            <p className="eyebrow">Basar Soft</p>
            <h1>AI Workspace</h1>
          </div>
          <button
            type="button"
            className="ghost-button mobile-only"
            onClick={() => setSidebarOpen(false)}
          >
            Kapat
          </button>
        </div>

        <div className="sidebar-actions">
          <button
            type="button"
            className="action-button"
            onClick={() => handleCreateConversation('chat')}
          >
            Yeni sohbet
          </button>
          <button
            type="button"
            className="action-button action-button-secondary"
            onClick={() => handleCreateConversation('agent')}
          >
            Yeni agent
          </button>
        </div>

        <div className="conversation-list">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={`conversation-card ${
                conversation.id === activeConversation?.id ? 'conversation-card-active' : ''
              }`}
              onClick={() => handleSelectConversation(conversation.id)}
            >
              <div className="conversation-card-top">
                <span className={`mode-pill mode-pill-${conversation.mode}`}>
                  {conversation.mode === 'chat' ? 'Chat' : 'Agent'}
                </span>
                <span className="conversation-time">
                  {formatClock(conversation.updatedAt)}
                </span>
              </div>
              <strong>{conversation.title}</strong>
              <p>{getConversationPreview(conversation)}</p>
              <div className="conversation-card-actions">
                <span className="conversation-card-hint">
                  Silmek icin asagidaki butonu kullanin
                </span>
                <button
                  type="button"
                  className="conversation-delete"
                  onClick={(event) => {
                    event.stopPropagation()
                    void handleDeleteConversation(conversation.id)
                  }}
                >
                  Sil
                </button>
              </div>
            </button>
          ))}
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div className="workspace-title-row">
            <button
              type="button"
              className="ghost-button mobile-only"
              onClick={() => setSidebarOpen(true)}
            >
              Gecmis
            </button>

            <div>
              <p className="eyebrow">Tek sayfa AI chat ve agent deneyimi</p>
              <h2>
                {activeConversation?.mode === 'chat'
                  ? 'Prompt ve yanit odakli chat'
                  : 'User id ile durum koruyan agent'}
              </h2>
            </div>
          </div>

          <div className="toolbar">
            <div className="mode-toggle" role="tablist" aria-label="Mod secimi">
              <button
                type="button"
                className={activeConversation?.mode === 'chat' ? 'toggle-active' : ''}
                onClick={() => handleModeSwitch('chat')}
              >
                Chat modu
              </button>
              <button
                type="button"
                className={activeConversation?.mode === 'agent' ? 'toggle-active' : ''}
                onClick={() => handleModeSwitch('agent')}
              >
                Agent modu
              </button>
            </div>

            {activeConversation?.mode === 'agent' && activeConversation.userId ? (
              <div className="session-chip">user_id: {activeConversation.userId}</div>
            ) : null}

            <div className="toolbar-actions">
              {activeConversation?.mode === 'agent' ? (
                <button
                  type="button"
                  className="ghost-button"
                  disabled={isSyncingHistory}
                  onClick={() => void handleSyncAgentHistory()}
                >
                  {isSyncingHistory ? 'Yenileniyor...' : 'Gecmisi yenile'}
                </button>
              ) : null}
            </div>
          </div>
        </header>

        <section className="message-stream">
          {activeConversation?.messages.length ? (
            activeConversation.messages.map((message) => (
              <article
                key={message.id}
                className={`message-row ${
                  message.role === 'assistant' ? 'message-row-assistant' : 'message-row-user'
                }`}
              >
                <div className="message-avatar">
                  {message.role === 'assistant' ? 'AI' : 'HU'}
                </div>

                <div className="message-card">
                  <div className="message-head">
                    <strong>
                      {message.role === 'assistant' ? 'Asistan' : 'Kullanici'}
                    </strong>
                    <span>{formatClock(message.createdAt)}</span>
                  </div>
                  <p className="message-content">{message.content}</p>

                  {message.meta?.intent ? (
                    <div className="message-panel">
                      <div className="panel-head">
                        <strong>Niyet analizi</strong>
                        {typeof message.meta.intent.confidence === 'number' ? (
                          <span>
                            Guven: %{Math.round(message.meta.intent.confidence * 100)}
                          </span>
                        ) : null}
                      </div>
                      <div className="intent-grid">
                        <div>
                          <span className="muted-label">Intent</span>
                          <strong>{message.meta.intent.intent || 'Belirtilmedi'}</strong>
                        </div>
                        <div>
                          <span className="muted-label">Dil</span>
                          <strong>{message.meta.intent.language || 'Belirtilmedi'}</strong>
                        </div>
                        {message.meta.answerTimeMs ? (
                          <div>
                            <span className="muted-label">YanIt suresi</span>
                            <strong>{message.meta.answerTimeMs} ms</strong>
                          </div>
                        ) : null}
                        {typeof message.meta.totalFound === 'number' ? (
                          <div>
                            <span className="muted-label">Bulunan urun</span>
                            <strong>{message.meta.totalFound}</strong>
                          </div>
                        ) : null}
                      </div>

                      {message.meta.intent.filters ? (
                        <div className="filter-badges">
                          {Object.entries(message.meta.intent.filters).map(([key, value]) => {
                            if (
                              value === null ||
                              value === undefined ||
                              value === '' ||
                              (Array.isArray(value) && value.length === 0)
                            ) {
                              return null
                            }

                            const label = Array.isArray(value)
                              ? value.join(', ')
                              : String(value)

                            return (
                              <span key={key} className="filter-pill">
                                {key}: {label}
                              </span>
                            )
                          })}
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  {message.meta?.products?.length ? (
                    <div className="product-grid">
                      {message.meta.products.map((product) => (
                        <div key={product.id} className="product-card">
                          <div className="product-head">
                            <strong>{product.name}</strong>
                            <span>{product.brand || 'Marka yok'}</span>
                          </div>
                          <div className="price-row">
                            <strong>{product.price} TL</strong>
                            {product.discount_rate ? (
                              <span>-%{product.discount_rate}</span>
                            ) : null}
                          </div>
                          <p>{product.description}</p>
                          <div className="product-meta">
                            <span>{product.category}</span>
                            <span>{product.color || 'Renk yok'}</span>
                            <span>{product.season || 'Sezon yok'}</span>
                            <span>Stok: {product.stock_quantity ?? 0}</span>
                          </div>
                          {parseArrayLike(product.features).length ? (
                            <div className="filter-badges">
                              {parseArrayLike(product.features).map((feature) => (
                                <span key={feature} className="filter-pill">
                                  {feature}
                                </span>
                              ))}
                            </div>
                          ) : null}
                          {parseArrayLike(product.sizes).length ? (
                            <div className="muted-copy">
                              Bedenler: {parseArrayLike(product.sizes).join(', ')}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">
              <p className="eyebrow">Hazir</p>
              <h3>
                {activeConversation?.mode === 'chat'
                  ? 'Tek bir prompt gonderin, yaniti aninda alin.'
                  : 'Agent oturumu hazir. Her yeni prompt ayni user_id ile gidecek.'}
              </h3>
              <p>
                Eski konusmalar localStorage icinde tutulur ve tekrar girdiginizde solda listelenir.
              </p>
            </div>
          )}

          {isSending ? (
            <article className="message-row message-row-assistant">
              <div className="message-avatar">AI</div>
              <div className="message-card typing-card">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </article>
          ) : null}
        </section>

        <footer className="composer-shell">
          <form className="composer" onSubmit={sendMessage}>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleInputKeyDown}
              rows={1}
              maxLength={4000}
              placeholder={
                activeConversation?.mode === 'chat'
                  ? 'Sorunuzu yazin...'
                  : 'Agent icin yeni yonlendirme yazin...'
              }
            />
            <div className="composer-footer">
              <p>
                Sadece metin kabul edilir. Medya dosyasi veya ek yukleme desteklenmez.
              </p>
              <button type="submit" className="send-button" disabled={isSending || !draft.trim()}>
                {isSending ? 'Gonderiliyor...' : 'Gonder'}
              </button>
            </div>
          </form>
        </footer>
      </main>

      {sidebarOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Kenarligi kapat"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="toast-stack" aria-live="polite" aria-atomic="true">
        {toasts.map((toast) => (
          <div key={toast.id} className="toast-card" role="alert">
            <div>
              <strong>{toast.title}</strong>
              <p>{toast.description}</p>
            </div>
            <button
              type="button"
              className="toast-close"
              onClick={() =>
                setToasts((current) => current.filter((item) => item.id !== toast.id))
              }
            >
              X
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
