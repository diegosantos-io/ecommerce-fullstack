
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Carrinho from './Carrinho'
import { apiRequest } from '../services/api'

vi.mock('../services/api', () => ({
  apiRequest: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const produto = {
  id: 1,
  nome: 'Teclado Mecânico',
  descricao: 'Teclado para jogos',
  preco: 199.9,
  estoque: 5,
  categoria_id: 2,
  ativo: true,
  imagem_url: '',
}

function renderizarCarrinho() {
  return render(
    <MemoryRouter>
      <Carrinho />
    </MemoryRouter>,
  )
}

describe('Carrinho de compras', () => {
  it('mostra o estado de carregamento', () => {
    apiRequest.mockReturnValue(new Promise(() => {}))

    renderizarCarrinho()

    expect(screen.getByText('Carregando seu carrinho...')).toBeInTheDocument()
  })

  it('exibe o produto e calcula o subtotal', async () => {
    apiRequest
      .mockResolvedValueOnce({
        itens: [{ id: 10, produto_id: 1, quantidade: 2 }],
      })
      .mockResolvedValueOnce([produto])

    renderizarCarrinho()

    expect(
      await screen.findByRole('heading', { name: 'Teclado Mecânico' }),
    ).toBeInTheDocument()

    expect(screen.getAllByText('R$ 399,80')).toHaveLength(2)
    expect(screen.getByRole('button', { name: /finalizar compra/i })).toBeEnabled()
  })

  it('mostra uma mensagem quando o carrinho está vazio', async () => {
    apiRequest
      .mockResolvedValueOnce({ itens: [] })
      .mockResolvedValueOnce([produto])

    renderizarCarrinho()

    expect(
      await screen.findByRole('heading', { name: 'Seu carrinho está vazio' }),
    ).toBeInTheDocument()
  })

  it('mostra erro quando a API falha', async () => {
    apiRequest.mockRejectedValue(new Error('Falha ao carregar carrinho'))

    renderizarCarrinho()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Falha ao carregar carrinho',
    )
  })
})
